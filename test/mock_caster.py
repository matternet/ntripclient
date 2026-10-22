#!/usr/bin/env python3
"""Minimal NTRIP v2 mock caster for OS-568 bench tests.

Scenarios (first arg):
  normal   stream RTCM-ish frames at 1 Hz forever
  pause    stream 5 s, go silent, resume only after a GGA arrives
           (and at least PAUSE_SEC elapsed); client must keep sending GGA
  stall    stream 5 s, then go silent forever (session stays open)
  chunkext chunked encoding; every chunk carries an extension ";foo=bar"
  noresp   accept TCP, never send a response header
  flush    stream 5 s, go silent for FLUSH_SEC while buffering frames, then
           send the whole backlog at once and continue (LOG-2092 pattern)
Second arg: port.
Logs to stderr with timestamps. Prints GGA lines it receives.
"""
import socket, sys, time, threading, select

PAUSE_SEC = 8
FLUSH_SEC = 25

def log(msg):
    sys.stderr.write(time.strftime("%H:%M:%S ") + "caster: " + msg + "\n")
    sys.stderr.flush()

def frame(n):
    # Fake RTCM3 frame: preamble 0xD3 + 2-byte length + payload + 3 crc bytes
    payload = (b"%08d" % n) * 3
    return b"\xd3" + bytes([0, len(payload)]) + payload + b"\x00\x00\x00"

def read_header(conn):
    data = b""
    conn.settimeout(10)
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(1024)
        if not chunk:
            return None
        data += chunk
    return data

def gga_pump(conn, state):
    """Background reader: consume client->server bytes (GGA) and flag them."""
    conn.setblocking(False)
    buf = b""
    while not state["done"]:
        r, _, _ = select.select([conn], [], [], 0.2)
        if not r:
            continue
        try:
            d = conn.recv(4096)
        except BlockingIOError:
            continue
        except OSError:
            break
        if not d:
            break
        buf += d
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            line = line.strip()
            if line.startswith(b"$GPGGA"):
                state["gga_count"] += 1
                state["last_gga"] = time.time()
                log("GGA #%d: %s" % (state["gga_count"], line[:40].decode(errors="replace")))

def serve(conn, scenario):
    state = {"done": False, "gga_count": 0, "last_gga": 0}
    hdr = read_header(conn)
    if hdr is None:
        return
    log("request: " + hdr.split(b"\r\n")[0].decode(errors="replace"))
    if scenario == "noresp":
        log("noresp: holding connection open with no response")
        time.sleep(600)
        return
    chunked = scenario == "chunkext"
    resp = (b"HTTP/1.1 200 OK\r\nNtrip-Version: Ntrip/2.0\r\nServer: mock\r\n"
            b"Content-Type: gnss/data\r\n" +
            (b"Transfer-Encoding: chunked\r\n" if chunked else b"") +
            b"\r\n")
    conn.sendall(resp)
    t = threading.Thread(target=gga_pump, args=(conn, state), daemon=True)
    t.start()
    n = 0
    start = time.time()
    paused_at = None
    try:
        while True:
            now = time.time()
            if scenario in ("pause", "stall") and now - start > 5:
                if paused_at is None:
                    paused_at = now
                    log("%s: going silent" % scenario)
                if scenario == "stall":
                    time.sleep(0.5)
                    continue
                # pause: resume only after PAUSE_SEC and a GGA received during the pause
                if now - paused_at < PAUSE_SEC or state["last_gga"] < paused_at:
                    time.sleep(0.2)
                    continue
                log("pause: GGA seen during pause (%d total), resuming" % state["gga_count"])
                start = now  # don't pause again
                paused_at = None
            if scenario == "flush" and now - start > 5:
                if paused_at is None:
                    paused_at = now
                    backlog = b""
                    log("flush: going silent, buffering frames")
                if now - paused_at < FLUSH_SEC:
                    n += 1
                    backlog += frame(n)
                    time.sleep(1.0)
                    continue
                log("flush: sending %d B backlog at once (%d frames)" % (len(backlog), n))
                conn.sendall(backlog)
                start = now
                paused_at = None
            n += 1
            f = frame(n)
            if chunked:
                conn.sendall(b"%x;foo=bar\r\n" % len(f) + f + b"\r\n")
            else:
                conn.sendall(f)
            time.sleep(1.0)
    except (BrokenPipeError, ConnectionResetError, OSError) as e:
        log("client gone: %s" % e)
    finally:
        state["done"] = True

def main():
    scenario, port = sys.argv[1], int(sys.argv[2])
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(5)
    log("listening on %d scenario=%s" % (port, scenario))
    while True:
        conn, addr = srv.accept()
        log("accepted connection from %s:%d" % addr)
        threading.Thread(target=serve, args=(conn, scenario), daemon=True).start()

if __name__ == "__main__":
    main()
