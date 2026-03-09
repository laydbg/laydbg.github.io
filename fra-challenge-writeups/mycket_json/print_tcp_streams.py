import subprocess
import sys


def run_command(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE).stdout.decode(
        "utf-8"
    )


def merge_consecutive_streams(streams):
    if not streams:
        return []

    merged = [streams[0]]
    for curr in streams[1:]:
        prev = merged[-1]
        if curr["src"] == prev["src"] and curr["dst"] == prev["dst"]:
            prev["msgs"].extend(curr["msgs"])
        else:
            merged.append(curr)

    return merged


def parse_tcp_stream(stream):
    lines = stream.splitlines()

    src = lines[4][8:].split(":")[0]
    dst = lines[5][8:].split(":")[0]
    msgs = []
    for i in range(6, len(lines) - 2, 2):
        if lines[i].startswith("\t"):
            msgs.append(("in", lines[i + 1]))
        else:
            msgs.append(("out", lines[i + 1]))
    return {"src": src, "dst": dst, "msgs": msgs}


def get_tcp_stream(pcap_file, stream_idx):
    cmd = f"tshark -r {pcap_file} -q -z follow,tcp,ascii,{stream_idx}"
    return parse_tcp_stream(run_command(cmd))


def get_tcp_stream_idxs(pcap_file, ip):
    cmd = f"tshark -r {pcap_file} -Y 'ip.addr=={ip}' -T fields -e tcp.stream | uniq"
    return run_command(cmd).splitlines()


def print_messages(msgs):
    if not msgs:
        return

    # Print the first message
    dir, msg = msgs[0]
    if dir == "out":
        print(f"    ---------> {msg}")
    else:
        print(f"    <--------- {msg}")

    i = 1
    n = len(msgs)
    while i < n:
        if i + 1 >= n:
            # Leftover single message
            dir, msg = msgs[i]
            if dir == "out":
                print(f"    ---------> {msg}")
            else:
                print(f"    <--------- {msg}")
            break

        pair = msgs[i : i + 2]
        count = 1
        i += 2

        while i + 1 < n and msgs[i : i + 2] == pair:
            count += 1
            i += 2

        if count == 1:  # No duplicates
            for dir, msg in pair:
                if dir == "out":
                    print(f"    ---------> {msg}")
                else:
                    print(f"    <--------- {msg}")
        else:
            dir1, msg1 = pair[0]
            if dir1 == "out":
                print(f"      |------> {msg1}")
            else:
                print(f"      |<------ {msg1}")

            dir2, msg2 = pair[1]
            if dir2 == "out":
                print(f"  {'x'+str(count):>4}|------> {msg2}")
            else:
                print(f"  {'x'+str(count):>4}|<------ {msg2}")


def print_tcp_streams(pcap_file, ip):
    streams = [
        get_tcp_stream(pcap_file, idx) for idx in get_tcp_stream_idxs(pcap_file, ip)
    ]
    streams = merge_consecutive_streams(streams)

    if not streams:
        return

    print(f"#######{'#'*len(ip)}#######")
    print(f"###### {ip} ######")
    print(f"#######{'#'*len(ip)}#######")
    for stream in streams:
        print(f"Src: {stream['src']}, Dst: {stream['dst']}:")
        print_messages(stream["msgs"])
    print()


def get_tcp_initiators(pcap_file):
    cmd = f"tshark -r {pcap_file} -Y 'tcp.flags==0x0002' -T fields -e ip.src | sort -u"
    return run_command(cmd).splitlines()


def main(pcap_file, output_dir="out"):
    initiators = get_tcp_initiators(pcap_file)
    initiators.sort(key=lambda ip: tuple(map(int, ip.split("."))))

    for ip in initiators:
        print_tcp_streams(pcap_file, ip)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_pcap>")
        sys.exit(1)

    pcap_file = sys.argv[1]
    main(pcap_file)
