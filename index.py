import requests
import os
import ipaddress
import argparse
import sys

AMAZON_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
OUTPUT_FOLDER = "target"
MIN_PREFIXES = 1000  # Amazon publishes ~8000 IPv4 prefixes, less than this means the data is broken


def download_amazon_ranges():
    print("[+] Downloading...")
    r = requests.get(AMAZON_URL, timeout=10)
    r.raise_for_status()
    return r.json()


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
    with open(tmp_file, "w") as f:
        for line in items:
            f.write(line + "\n")
    os.replace(tmp_file, output_file)

    print(f"[✓] Done! File generated : {output_file}")


def ask_user_choice():
    print("What do you want to extract?")
    print("[1] All IP addresses (expand CIDRs) NOTE: The generated file is about 1.5 GB")
    print("[2] Keep the original CIDR subnets")
    print("[3] Original CIDR subnets, without the ones already included in a bigger one")
    print("[4] Compact CIDR subnets (overlapping and adjacent ones merged, shortest list)")
    while True:
        choice = input("> ").strip()
        if choice in ("1", "2", "3", "4"):
            return choice
        print("Please enter 1, 2, 3 or 4.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Amazon ip-ranges.json into a raw list. Without argument, asks what to extract."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--expand", action="store_true", help="all IP addresses (same as choice 1)")
    mode.add_argument("--cidr", action="store_true", help="original CIDR subnets (same as choice 2)")
    mode.add_argument("--dedupe", action="store_true", help="CIDR subnets without the nested ones (same as choice 3)")
    mode.add_argument("--compact", action="store_true", help="merged CIDR subnets, shortest list (same as choice 4)")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.expand:
        choice = "1"
    elif args.cidr:
        choice = "2"
    elif args.dedupe:
        choice = "3"
    elif args.compact:
        choice = "4"
    else:
        choice = ask_user_choice()

    data = download_amazon_ranges()
    prefixes = extract_prefixes(data)
    check_prefixes(prefixes)

    if choice == "1":
        result = expand_ips(prefixes)
        output_file = os.path.join(OUTPUT_FOLDER, "amazon_ip_ranges_extended.txt")
    elif choice == "3":
        result = remove_nested(prefixes)
        output_file = os.path.join(OUTPUT_FOLDER, "amazon_ip_ranges_dedupe.txt")
    elif choice == "4":
        result = merge_subnets(prefixes)
        output_file = os.path.join(OUTPUT_FOLDER, "amazon_ip_ranges_compact.txt")
    else:
        result = sorted(prefixes, key=ipaddress.ip_network)  # numeric order, not text order
        output_file = os.path.join(OUTPUT_FOLDER, "amazon_ip_ranges.txt")

    write_list(result, output_file)


if __name__ == "__main__":
    main()
