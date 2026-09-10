"""Caller contracts against the selected firmware Python; no C, GC, crypto or device runs."""

import argparse
import sys
import types
import unittest
import json
from itertools import product
from pathlib import Path
from unittest.mock import patch


INPUT = b"opaque input:" * 120
SIGNED = b"opaque signed response:" * 110


class ActionCancelled(Exception):
    pass


class DataError(Exception):
    pass


class ProcessError(Exception):
    pass


class TaskStopped(BaseException):
    """An exception outside Exception, as required for unconditional cleanup."""


class Pause:
    def __await__(self):
        yield self


class Message:
    def __init__(self, **fields):
        self.__dict__.update(fields)

    @classmethod
    def is_type_of(cls, value):
        return isinstance(value, cls)


def module(name, **attributes):
    result = types.ModuleType(name)
    result.__dict__.update(attributes)
    return result


class CallerStubs:
    """Only the imported firmware boundaries are replaced; both callers stay real."""

    def __init__(self):
        self.pending = None
        self.generation = 0
        self.fault = None
        self.fail_layout = 0
        self.confirmed = []
        self.layouts = []
        self.sign_calls = []
        self.sign_completed = 0
        self.cancel_calls = 0
        self.sent = []
        self.requests = []
        self.deadlines = []
        self.workflow_closes = 0
        self.pause = Pause()
        self.messages = module("trezor.messages", **{
            name: type(name, (Message,), {}) for name in (
                "IronwoodPcztAck", "IronwoodPcztRequest", "IronwoodSignedPczt",
                "IronwoodSignedPcztAck", "Success",
            )
        })
        self.ironwood = module("ironwood_test", begin=self.begin, sign=self.sign,
                               cancel=self.cancel)
        self.utils = module("trezor.utils", EMULATOR=True, INTERNAL_MODEL="T3T1",
                            UI_LAYOUT="DELIZIA", USE_THP=False, IRONWOOD_NATIVE_CALLER=False)
        self.usb = module("usb", iface_wire=object())
        self.ctx = types.SimpleNamespace(iface=self.usb.iface_wire)
        self.context = module("trezor.wire.context", get_context=lambda: self.ctx,
                              call=self.call, with_context=self.with_context)
        self.loop = module("trezor.loop", this_task=object(), sleep=self.sleep,
                           race=self.race, schedule=self.deadlines.append, close=self.close)
        self.layouts_module = module("trezor.ui.layouts",
                                     confirm_properties=self.confirm_properties,
                                     confirm_value=self.confirm_value,
                                     confirm_action=self.confirm_action)
        self.modules = {
            "micropython": module("micropython", const=lambda value: value),
            "ironwood_test": self.ironwood,
            "usb": self.usb,
            "trezor": module("trezor", loop=self.loop, utils=self.utils,
                              workflow=module("trezor.workflow", close_others=self.close_others)),
            "trezor.crypto": module("trezor.crypto", random=types.SimpleNamespace(
                bytes=lambda length: b"t" * length)),
            "trezor.messages": self.messages,
            "trezor.enums": module("trezor.enums", ButtonRequestType=types.SimpleNamespace(
                Other=1, ConfirmOutput=2, SignTx=3),
                MessageType=types.SimpleNamespace(IronwoodSignPczt=1)),
            "trezor.wire": module("trezor.wire", ActionCancelled=ActionCancelled,
                                  DataError=DataError, ProcessError=ProcessError,
                                  context=self.context),
            "trezor.ui": module("trezor.ui"),
            "trezor.ui.layouts": self.layouts_module,
            "apps": module("apps"),
            "apps.zcash": module("apps.zcash"),
        }

    def load(self, optimize=0):
        for name in ("ironwood_review", "sign_pczt"):
            qualified = "apps.zcash." + name
            loaded = module(qualified)
            sys.modules[qualified] = loaded
            path = SOURCE_DIR / (name + ".py")
            exec(compile(path.read_bytes(), str(path), "exec", optimize=optimize),
                 loaded.__dict__)
            setattr(self, name, loaded)

    def begin(self, raw):
        # C cancels the previous review, then Rust retains a parsed request before
        # the C review dict/bytes allocations. Do not auto-clean the injected error.
        self.pending = None
        self.generation += 1
        self.token = self.generation.to_bytes(32, "big")
        self.pending = self.token
        self.raw = bytes(raw)
        if self.fault == "begin_memory":
            raise MemoryError("review allocation after Rust retained request")
        return {
            "token": self.token, "network": "regtest (synthetic)", "pool": "Ironwood",
            "total_input": 100000000, "payments": 70000000, "change": 29999000,
            "fee": 1000, "expiry": 200,
            "outputs": (
                {"kind": "Payment", "value": 70000000, "receiver": b"p" * 43},
                {"kind": "InternalChange", "value": 29999000, "receiver": b"c" * 43},
            ),
        }

    def sign(self, token):
        # Observe UI ordering here; do not enforce it in the stub and mask a bug.
        self.sign_calls.append((token, list(self.confirmed)))
        if self.fault == "response_memory":
            raise MemoryError("vstr allocation before Rust consumes request")
        pending, self.pending = self.pending, None
        if len(token) != 32 or token != pending:
            raise ValueError("invalid review token")
        if self.fault == "sign_rejected":
            raise ValueError("synthetic signing failed")
        self.sign_completed += 1
        if self.fault == "header_memory":
            raise MemoryError("bytes header after Rust signing returned")
        return SIGNED

    def cancel(self):
        self.cancel_calls += 1
        self.pending = None

    async def confirm(self, kind, fields):
        index = len(self.layouts)
        self.layouts.append((kind, fields))
        if index == self.fail_layout:
            if self.fault == "layout_memory":
                raise MemoryError("layout allocation")
            if self.fault == "layout_cancel":
                raise ActionCancelled("layout cancelled")
            if self.fault == "layout_base":
                raise TaskStopped("layout task stopped")
            if self.fault == "layout_close":
                await self.pause
        self.confirmed.append(fields["br_name"])
        # Firmware layout helpers return None only after confirmation.

    async def confirm_properties(self, **fields):
        await self.confirm("properties", fields)

    async def confirm_value(self, **fields):
        await self.confirm("value", fields)

    async def confirm_action(self, **fields):
        await self.confirm("action", fields)

    async def with_context(self, ctx, coroutine):
        assert ctx is self.ctx
        return await coroutine

    async def sleep(self, milliseconds):
        await self.pause

    async def race(self, call, timer):
        # Deterministic I/O branch; no clock or MicroPython scheduling model.
        try:
            return await call
        finally:
            timer.close()

    def close(self, coroutine):
        coroutine.close()
        if self.fault == "deadline_close":
            raise TaskStopped("deadline cleanup failed")

    def close_others(self):
        self.workflow_closes += 1

    async def call(self, message, expected_type):
        if isinstance(message, self.messages.IronwoodPcztRequest):
            self.requests.append(message)
            return self.messages.IronwoodPcztAck(
                transfer_id=message.transfer_id, offset=message.offset,
                data=INPUT[message.offset:message.offset + message.length])
        assert isinstance(message, self.messages.IronwoodSignedPczt)
        self.sent.append(message)
        if self.fault == "ack_failure":
            raise ActionCancelled("outgoing ACK failed")
        if self.fault == "ack_timeout":
            return None  # The race's timeout winner has this value.
        return self.messages.IronwoodSignedPcztAck(
            transfer_id=message.transfer_id,
            next_offset=message.offset + len(message.data) + (self.fault == "bad_ack"))


class CallerCleanupTests(unittest.TestCase):
    def setUp(self):
        self.stub = CallerStubs()
        self.modules = patch.dict(sys.modules, self.stub.modules)
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.stub.load()

    def finish(self, coroutine):
        try:
            yielded = coroutine.send(None)
        except StopIteration as done:
            return done.value
        else:
            coroutine.close()
            self.fail(f"unexpected suspension: {yielded!r}")

    def transfer(self):
        return self.stub.sign_pczt._transfer(Message(total_length=len(INPUT)))

    def assert_signed_after_all_layouts(self, expected_token):
        self.assertEqual(self.stub.sign_calls, [(expected_token, [
            "ironwood_test_context", "ironwood_test_output", "ironwood_test_receiver",
            "ironwood_test_output", "ironwood_test_receiver", "ironwood_test_totals",
            "ironwood_test_sign",
        ])])
        receivers = [fields for kind, fields in self.stub.layouts if kind == "value"]
        self.assertEqual([fields["value"] for fields in receivers],
                         [(b"p" * 43).hex(), (b"c" * 43).hex()])
        for fields in receivers:
            self.assertTrue(fields["is_data"])
            self.assertFalse(fields["chunkify"])
        self.assertTrue(self.stub.layouts[-1][1]["hold"])

    def assert_released(self):
        self.assertIsNone(self.stub.pending)
        self.assertGreater(self.stub.cancel_calls, 0)
        for deadline in self.stub.deadlines:
            self.assertIsNone(deadline.cr_frame)

    def recover(self):
        # Preserve the same bridge/token counter so recovery is not a fresh mock.
        self.stub.fault = None
        self.stub.layouts.clear()
        self.stub.confirmed.clear()
        self.stub.sign_calls.clear()
        self.stub.sent.clear()
        result = self.finish(self.transfer())
        self.assertIsInstance(result, self.stub.messages.Success)
        self.assertEqual(b"".join(part.data for part in self.stub.sent), SIGNED)
        self.assert_signed_after_all_layouts(self.stub.token)
        self.assert_released()

    def test_successful_transfer(self):
        self.recover()
        self.assertEqual(self.stub.raw, INPUT)
        self.assertEqual(self.stub.cancel_calls, 2)
        self.assertEqual([part.offset for part in self.stub.sent], [0, 1024, 2048])
        self.assertEqual([part.offset for part in self.stub.requests], [0, 1024])
        self.assertTrue(all(part.transfer_id == b"t" * 16 for part in self.stub.sent))

    def test_begin_memory_error_after_retention(self):
        self.stub.fault = "begin_memory"
        with self.assertRaisesRegex(MemoryError, "retained request"):
            self.finish(self.transfer())
        self.assertEqual(self.stub.generation, 1)
        self.assertEqual(self.stub.cancel_calls, 1)  # Only the outer finally ran.
        self.assertEqual(self.stub.sign_calls, [])
        self.assertEqual(self.stub.sent, [])
        self.assert_released()
        self.recover()

    def test_each_layout_failure_and_coroutine_close(self):
        errors = {"layout_memory": MemoryError, "layout_cancel": ActionCancelled,
                  "layout_base": TaskStopped, "layout_close": GeneratorExit}
        for direct in (False, True):
            for fault, error in errors.items():
                for index in range(7):
                    with self.subTest(direct_review=direct, fault=fault, layout=index):
                        self.stub.layouts.clear()
                        self.stub.confirmed.clear()
                        self.stub.sign_calls.clear()
                        self.stub.sent.clear()
                        self.stub.fault, self.stub.fail_layout = fault, index
                        cancelled = self.stub.cancel_calls
                        coroutine = (self.stub.ironwood_review.review_and_sign(
                            self.stub.begin(INPUT)) if direct else self.transfer())
                        if fault == "layout_close":
                            self.assertIs(coroutine.send(None), self.stub.pause)
                            self.assertIsNotNone(self.stub.pending)
                            self.assertEqual(self.stub.sign_calls, [])
                            self.assertIsNone(coroutine.close())
                        else:
                            with self.assertRaises(error):
                                self.finish(coroutine)
                        self.assertEqual(len(self.stub.confirmed), index)
                        self.assertEqual(self.stub.sign_calls, [])
                        self.assertEqual(self.stub.sent, [])
                        self.assertEqual(self.stub.cancel_calls - cancelled, 1 if direct else 2)
                        self.assert_released()
                        self.recover()

    def test_sign_failures(self):
        for direct in (False, True):
            for fault in ("response_memory", "header_memory", "sign_rejected"):
                with self.subTest(direct_review=direct, fault=fault):
                    self.stub.layouts.clear()
                    self.stub.confirmed.clear()
                    self.stub.sign_calls.clear()
                    self.stub.sent.clear()
                    self.stub.fault = fault
                    completed = self.stub.sign_completed
                    cancelled = self.stub.cancel_calls
                    coroutine = (self.stub.ironwood_review.review_and_sign(
                        self.stub.begin(INPUT)) if direct else self.transfer())
                    with self.assertRaises(ValueError if fault == "sign_rejected" else MemoryError):
                        self.finish(coroutine)
                    self.assert_signed_after_all_layouts(self.stub.token)
                    self.assertEqual(self.stub.sign_completed - completed, fault == "header_memory")
                    self.assertEqual(self.stub.sent, [])
                    self.assertEqual(self.stub.cancel_calls - cancelled, 1 if direct else 2)
                    self.assert_released()
                    self.recover()

    def test_invalid_and_stale_tokens(self):
        for kind in ("short", "mismatched", "stale"):
            with self.subTest(token=kind):
                self.stub.layouts.clear()
                self.stub.confirmed.clear()
                self.stub.sign_calls.clear()
                self.stub.sent.clear()
                old = self.stub.begin(INPUT)
                review = self.stub.begin(INPUT)
                bad = {"short": b"x", "mismatched": b"x" * 32,
                       "stale": old["token"]}[kind]
                review["token"] = bad
                with self.assertRaisesRegex(ValueError, "invalid review token"):
                    self.finish(self.stub.ironwood_review.review_and_sign(review))
                self.assert_signed_after_all_layouts(bad)
                self.assertEqual(self.stub.sent, [])
                self.assert_released()
                self.recover()

    def test_outgoing_ack_failures(self):
        for fault, error in (("ack_failure", ActionCancelled), ("ack_timeout", ActionCancelled),
                             ("bad_ack", DataError)):
            with self.subTest(fault=fault):
                self.stub.layouts.clear()
                self.stub.confirmed.clear()
                self.stub.sign_calls.clear()
                self.stub.sent.clear()
                self.stub.fault = fault
                with self.assertRaises(error):
                    self.finish(self.transfer())
                self.assert_signed_after_all_layouts(self.stub.token)
                self.assertEqual(len(self.stub.sent), 1)  # Signing and one send preceded failure.
                self.assert_released()
                self.recover()

    def test_cancel_even_when_deadline_cleanup_raises(self):
        self.stub.fault = "deadline_close"
        with self.assertRaises(TaskStopped):
            self.finish(self.transfer())
        self.assert_released()
        self.recover()

    def test_runtime_capability_matrix(self):
        # An explicit accepted-case table, including the deliberate optimized
        # native route. A false compile-feature boolean retains emulator-only behavior.
        accepted = {
            (0, False, True, "T3T1", "DELIZIA", False),
            (0, False, True, "T3W1", "ECKHART", True),
            (0, True, False, "T3T1", "DELIZIA", False),
            (1, True, False, "T3T1", "DELIZIA", False),
        }
        for case in product((0, 1), (False, True), (False, True),
                            ("T3T1", "T3W1", "T2T1"),
                            ("DELIZIA", "ECKHART", "BOLT"), (False, True)):
            with self.subTest(runtime=case):
                optimize, marker, emulator, model, layout, thp = case
                self.stub.utils.IRONWOOD_NATIVE_CALLER = marker
                self.stub.utils.EMULATOR = emulator
                self.stub.utils.INTERNAL_MODEL = model
                self.stub.utils.UI_LAYOUT = layout
                self.stub.utils.USE_THP = thp
                self.stub.load(optimize=optimize)
                allowed = case in accepted
                self.assertEqual(self.stub.sign_pczt._supported_runtime(), allowed)
                self.assertFalse(hasattr(self.stub.sign_pczt, "boot"))
                before = self.stub.generation
                coroutine = self.stub.sign_pczt.sign_pczt(Message(total_length=len(INPUT)))
                if allowed:
                    self.assertIsInstance(self.finish(coroutine), self.stub.messages.Success)
                    self.assert_released()
                else:
                    with self.assertRaises(ProcessError):
                        self.finish(coroutine)
                    self.assertEqual(self.stub.generation, before)

    def test_primary_interface_required_for_both_routes(self):
        for native in (False, True):
            with self.subTest(native=native):
                self.stub.utils.IRONWOOD_NATIVE_CALLER = native
                self.stub.utils.EMULATOR = not native
                self.stub.ctx.iface = object()
                before = self.stub.generation
                with self.assertRaisesRegex(ProcessError, "Primary wire"):
                    self.finish(self.stub.sign_pczt.sign_pczt(Message(total_length=len(INPUT))))
                self.assertEqual(self.stub.generation, before)
        self.assertEqual(self.stub.workflow_closes, 0)

    def test_optimized_missing_workflow_owner(self):
        self.stub.utils.IRONWOOD_NATIVE_CALLER = True
        self.stub.utils.EMULATOR = False
        self.stub.load(optimize=1)
        self.assertTrue(self.stub.sign_pczt._supported_runtime())
        for direct in (True, False):
            with self.subTest(direct_transfer=direct):
                self.stub.loop.this_task = None
                coroutine = (self.transfer() if direct else self.stub.sign_pczt.sign_pczt(
                    Message(total_length=len(INPUT))))
                with self.assertRaisesRegex(ProcessError, "^Registered workflow required$"):
                    self.finish(coroutine)
                self.assertEqual(self.stub.deadlines, [])
                self.assertEqual(self.stub.generation, 0)
                self.assertEqual(self.stub.cancel_calls, 0)
                self.assertEqual(self.stub.layouts, [])
                self.assertEqual(self.stub.requests, [])
                self.assertEqual(self.stub.sign_calls, [])
                self.assertEqual(self.stub.sent, [])
                self.assertIsNone(self.stub.pending)
        # The rejected entry started no request; a registered owner can proceed.
        self.stub.loop.this_task = object()
        self.recover()


class CountSubtests(unittest.TextTestResult):
    """Report successful parameter cases too; unittest normally prints only failures."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subtest_count = 0

    def addSubTest(self, test, subtest, error):
        self.subtest_count += 1
        super().addSubTest(test, subtest, error)

    def stopTestRun(self):
        super().stopTestRun()
        print(json.dumps({"tests": self.testsRun, "subtests": self.subtest_count,
                          "failures": len(self.failures), "errors": len(self.errors)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("firmware_root", type=Path,
                        help="root containing core/src/apps/zcash")
    args = parser.parse_args()
    SOURCE_DIR = args.firmware_root.resolve() / "core/src/apps/zcash"
    for name in ("sign_pczt.py", "ironwood_review.py"):
        if not (SOURCE_DIR / name).is_file():
            parser.error(f"missing firmware source: {SOURCE_DIR / name}")
    unittest.main(argv=[sys.argv[0]], testRunner=unittest.TextTestRunner(
        verbosity=2, resultclass=CountSubtests))
