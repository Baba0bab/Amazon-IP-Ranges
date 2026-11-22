import requests
import os
import ipaddress
import argparse
import sys

AMAZON_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
# Next to index.py, whatever folder the script is launched from
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target")
MIN_PREFIXES = 1000  # Amazon publishes ~8000 IPv4 prefixes, less than this means the data is broken


def download_amazon_ranges():
    print("[+] Downloading...")
    try:
        r = requests.get(AMAZON_URL, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:  # no network, timeout, HTTP error or invalid JSON
        sys.exit(f"[!] Download failed: {e}\n[!] Nothing written.")


def extract_prefixes(data):
    prefixes = set()
    print("[+] Extracting IPv4 prefixes (ip_prefix)...")
    for entry in data.get("prefixes", []):  # IPv4 section
        if "ip_prefix" in entry:
            prefixes.add(entry["ip_prefix"])
    return prefixes


def check_prefixes(prefixes):
    # Stop before writing anything, so a bad download never replaces a good file
    if len(prefixes) < MIN_PREFIXES:
        sys.exit(f"[!] Only {len(prefixes)} prefixes found (at least {MIN_PREFIXES} expected), nothing written.")
    for cidr in prefixes:
        try:
            ipaddress.IPv4Network(cidr)
        except ValueError:
            sys.exit(f"[!] Invalid prefix found: {cidr!r}, nothing written.")


def expand_ips(prefixes):
    print("[+] Expanding CIDR to individual IPs...")

    # Merge overlapping subnets so each IP is only generated once, already sorted
    networks = ipaddress.collapse_addresses(ipaddress.ip_network(cidr) for cidr in prefixes)

    # IPs are generated one by one while writing instead of being stored in memory
    for net in networks:
        for ip in net:  # every address of the subnet, network and broadcast included
            yield str(ip)


def remove_nested(prefixes):
    print("[+] Removing subnets already included in a bigger one...")

    # Sorted by start address, bigger subnet first: a nested subnet always comes right after its parent
    networks = sorted(ipaddress.ip_network(cidr) for cidr in prefixes)

    kept = []
    for net in networks:
        if kept and net.subnet_of(kept[-1]):
            continue
        kept.append(net)

    return [str(net) for net in kept]


def merge_subnets(prefixes):
    print("[+] Merging overlapping and adjacent subnets...")

    # collapse_addresses returns the smallest list of subnets covering the same IPs, already sorted
    networks = ipaddress.collapse_addresses(ipaddress.ip_network(cidr) for cidr in prefixes)
    return [str(net) for net in networks]


def write_list(items, output_file):
    print(f"[+] Writing {output_file}...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write to a temporary file first, the real file is only replaced once everything is written
    tmp_file = output_file + ".tmp"
    try:
        with open(tmp_file, "w") as f:
            for line in items:
                f.write(line + "\n")
        os.replace(tmp_file, output_file)
    except BaseException:  # also catches Ctrl+C
        # Don't leave a half-written temporary file behind
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        raise

    print(f"[OK] Done! File generated : {output_file}")


def sort_prefixes(prefixes):
    return sorted(prefixes, key=ipaddress.ip_network)  # numeric order, not text order


# Every mode in one place: choice number -> argument, menu text, --help text, function, output file
MODES = {
    "1": {
        "arg": "--expand",
        "menu": "All IP addresses (expand CIDRs) NOTE: The generated file is about 1.5 GB",
        "help": "all IP addresses",
        "function": expand_ips,
        "file": "amazon_ip_ranges_extended.txt",
    },
    "2": {
        "arg": "--cidr",
        "menu": "Keep the original CIDR subnets",
        "help": "original CIDR subnets",
        "function": sort_prefixes,
        "file": "amazon_ip_ranges.txt",
    },
    "3": {
        "arg": "--dedupe",
        "menu": "Original CIDR subnets, without the ones already included in a bigger one",
        "help": "CIDR subnets without the nested ones",
        "function": remove_nested,
        "file": "amazon_ip_ranges_dedupe.txt",
    },
    "4": {
        "arg": "--compact",
        "menu": "Compact CIDR subnets (overlapping and adjacent ones merged, shortest list)",
        "help": "merged CIDR subnets, shortest list",
        "function": merge_subnets,
        "file": "amazon_ip_ranges_compact.txt",
    },
}


def ask_user_choice():
    print("What do you want to extract?")
    for choice, mode in MODES.items():
        print(f"[{choice}] {mode['menu']}")

    choices = list(MODES)
    while True:
        choice = input("> ").strip()
        if choice in MODES:
            return choice
        print(f"Please enter {', '.join(choices[:-1])} or {choices[-1]}.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Amazon ip-ranges.json into a raw list. Without argument, asks what to extract."
    )
    group = parser.add_mutually_exclusive_group()
    for choice, mode in MODES.items():
        group.add_argument(
            mode["arg"], dest="choice", action="store_const", const=choice,
            help=f"{mode['help']} (same as choice {choice})",
        )
    return parser.parse_args()


def main():
    args = parse_args()
    choice = args.choice or ask_user_choice()
    mode = MODES[choice]

    data = download_amazon_ranges()
    prefixes = extract_prefixes(data)
    check_prefixes(prefixes)

    result = mode["function"](prefixes)
    write_list(result, os.path.join(OUTPUT_FOLDER, mode["file"]))


if __name__ == "__main__":
    main()
