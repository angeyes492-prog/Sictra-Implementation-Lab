# Rejected control transport repair v0.1

Scope: existing loopback OperationsHandler rejection, local candidate only.
Precedence remains Host/Origin/token/content-type/framing authorization before
JSON parsing or any service call. Positive authorized requests retain their
behavior; this adds no mutation, source, publication or activation authority.

Repeated Windows 10053 occurred when a forbidden POST's response was lost.
The handler previously closed with its request body unread. Repair the
demonstrable unread-body path without claiming all possible transport resets
have the same cause or retrying a denied command.

For a forbidden POST, emit and flush the existing 403 JSON before closing.
Discard, never parse/execute, at most a single correctly framed Content-Length
body of 0..16000 bytes. No transfer encoding or duplicate/invalid/oversized
length is drained. Use read1 chunks and a one-second total monotonic deadline
with remaining socket timeout; short/cancelled/slow bodies close without new
responses or service effects. Force connection closure, never reuse unread
bytes as another request. For oversized/invalid or cancelled requests, delivery
of a response is not guaranteed; authorization remains denied. This is a
bounded transport repair, not slow-client or production server validation.

Unit tests establish actual discard, no JSON parse, framing and timeout bounds,
socket cancellation, and no reads on non-POST/non-403 replies. Loopback tests
send a delayed bounded body after receiving rejection headers, prove full 403
and zero journal mutation, then verify an authorized pause still works. Retain
the original failing HTTP assertion unchanged and rerun full regression/CI.
Rollback removes the rejection discard; no schema or journal migration.
