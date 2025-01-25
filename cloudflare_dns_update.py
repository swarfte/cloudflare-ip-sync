import socket
import requests
import time
import logging
import yaml
from typing import Dict, Tuple, List

# Configure logging
logging.basicConfig(
    filename='cloudflare_dns_update.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def load_config(config_file='config.yaml'):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def get_current_ip() -> str:
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json()['ip']
    except Exception as e:
        logging.error(f"Failed to get current IP: {e}")
        return None


def get_cloudflare_dns_ip(api_token: str, zone_id: str, record_name: str) -> Tuple[str, str, bool]:
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            records = response.json().get("result", [])
            for record in records:
                if record["name"] == record_name:
                    return record["content"], record["id"], record["proxied"]
        return None, None, None
    except Exception as e:
        logging.error(f"Failed to get Cloudflare DNS IP for {record_name}: {e}")
        return None, None, None


def update_cloudflare_dns(api_token: str, zone_id: str, record_id: str,
                          record_name: str, new_ip: str, proxied: bool) -> bool:
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "A",
        "name": record_name,
        "content": new_ip,
        "ttl": 1,
        "proxied": proxied
    }
    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            logging.info(f"Updated {record_name} with proxy status: {'enabled' if proxied else 'disabled'}")
            return True
        else:
            logging.error(f"Update failed for {record_name}. Status code: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Failed to update Cloudflare DNS for {record_name}: {e}")
        return False


def process_domain(api_token: str, zone_id: str, domain: Dict, current_ip: str) -> None:
    record_name = domain['record_name']
    proxied = domain.get('proxied', False)  # Default to False if not specified

    cloudflare_ip, record_id, current_proxied = get_cloudflare_dns_ip(api_token, zone_id, record_name)

    if not cloudflare_ip or not record_id:
        logging.error(f"Could not fetch DNS information for {record_name}")
        return

    # Update if IP is different or proxy status changed
    if cloudflare_ip != current_ip or current_proxied != proxied:
        logging.info(f"Update needed for {record_name}:")
        if cloudflare_ip != current_ip:
            logging.info(f"- IP mismatch. Current: {current_ip}, Cloudflare: {cloudflare_ip}")
        if current_proxied != proxied:
            logging.info(f"- Proxy status change. Current: {current_proxied}, Desired: {proxied}")

        if update_cloudflare_dns(api_token, zone_id, record_id, record_name, current_ip, proxied):
            logging.info(f"Successfully updated DNS record for {record_name}")
        else:
            logging.error(f"Failed to update DNS record for {record_name}")
    else:
        logging.debug(f"No updates needed for {record_name}")


def main():
    try:
        config = load_config()
        api_token = config['api_token']
        zone_id = config['zone_id']
        check_interval = config.get('check_interval', 300)  # Default 5 minutes
        domains = config.get('domains', [])

        if not domains:
            logging.error("No domains configured in config.yaml")
            return

        logging.info(f"Starting DNS monitor for {len(domains)} domains")

        while True:
            current_ip = get_current_ip()
            if current_ip:
                for domain in domains:
                    process_domain(api_token, zone_id, domain, current_ip)
            else:
                logging.error("Failed to get current IP address")

            logging.debug(f"Sleeping for {check_interval} seconds")
            time.sleep(check_interval)

    except KeyboardInterrupt:
        logging.info("Script stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
