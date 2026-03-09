import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import pyshark
import subprocess
import sys
from datetime import datetime


def run_command(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE).stdout.decode(
        "utf-8"
    )


def main(pcap_file):
    # Get tcp src (initiator) and dst (acceptor) ips
    srcs = sorted(
        run_command(
            f"tshark -r {pcap_file} -Y 'tcp.flags==0x0002' -T fields -e ip.src | sort -u"
        ).splitlines(),
        key=lambda ip: list(map(int, ip.split("."))),
        reverse=True,
    )
    dsts = run_command(
        f"tshark -r {pcap_file} -Y 'tcp.flags==0x0002' -T fields -e ip.dst | sort -u"
    ).splitlines()

    # Parse pcap
    cap = pyshark.FileCapture(pcap_file, display_filter="ip")
    packet_data = []
    for packet in cap:
        try:
            timestamp = datetime.fromtimestamp(float(packet.sniff_timestamp))
            src_ip = packet.ip.src
            dst_ip = packet.ip.dst

            if src_ip in srcs and dst_ip in dsts:
                packet_data.append((timestamp, src_ip, dst_ip))
            elif src_ip in dsts and dst_ip in srcs:
                packet_data.append((timestamp, dst_ip, src_ip))
        except AttributeError:
            continue
    cap.close()

    # Plot
    df = pd.DataFrame(packet_data, columns=["timestamp", "src_ip", "dst_ip"])
    src_ip_to_y = {ip: i for i, ip in enumerate(srcs)}

    df["y_pos"] = df["src_ip"].map(
        src_ip_to_y
    )  # Map each source IP to its Y coordinate

    colors = plt.get_cmap("tab10", len(dsts))
    dst_color_map = {
        dst: colors(i) for i, dst in enumerate(dsts)
    }  # Map each destination IP to a color

    fig, ax = plt.subplots(figsize=(12, 6))
    for dst in dsts:
        sub_df = df[df["dst_ip"] == dst]
        ax.scatter(
            sub_df["timestamp"],
            sub_df["y_pos"],
            label=dst,
            color=dst_color_map[dst],
            s=25,
        )

    # Format
    ax.set_xlabel("Time")
    ax.set_ylabel("Target IP")
    ax.set_title("Network Traffic: TCP Communication Over Time")
    ax.legend(title="Command & Control IP")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.set_yticks(list(src_ip_to_y.values()))
    ax.set_yticklabels(srcs)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_pcap>")
        sys.exit(1)

    pcap_file = sys.argv[1]
    main(pcap_file)
