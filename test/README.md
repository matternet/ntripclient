# ntripclient bench tests (OS-556)

A small mock NTRIP v2 caster plus a runner that drives `ntripclient` the way MATE does
(HTTP mode, GGA piped to stdin at 1 Hz). No network or credentials needed.

    make
    python3 test/mock_caster.py <scenario> <port> &
    test/run_client.sh <port> <duration_sec> <outprefix>

Scenarios (`mock_caster.py` first argument) and expected behaviour:

| Scenario   | Caster behaviour                                              | Expect from ntripclient                                              |
|------------|---------------------------------------------------------------|----------------------------------------------------------------------|
| `normal`   | 1 Hz RTCM-like frames forever                                 | every byte delivered, GGA received by caster at 1 Hz                 |
| `stall`    | 5 s of data, then silent forever (session stays open)         | `data watchdog tripped` at 10 s, reconnect 1 s later, stream resumes |
| `pause`    | 5 s of data, silent 8 s, resumes only after a GGA arrives     | GGA keeps flowing during the pause, stream resumes, **no** reconnect |
| `chunkext` | chunked encoding, every chunk carries `;foo=bar` extension    | no hang, all data delivered                                          |
| `noresp`   | accepts TCP, never sends a response header                    | header timeout at 10 s, reconnect with 1/2/4/8 s backoff, no exit    |
| `flush`    | 5 s of data, silent 25 s buffering frames, then sends backlog | watchdog closes session at 10 s; backlog hits a dead socket; zero stale frames delivered |

`<outprefix>.err` holds the UTC-stamped log lines, `<outprefix>.rtcm` the RTCM bytes
(30 B per mock frame). The mock casters log received GGA lines to their stderr.
