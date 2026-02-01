import requests

# Fetch disposable email domains from
# https://github.com/disposable-email-domains/disposable-email-domains

blocklist_url = 'https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/refs/heads/main/disposable_email_blocklist.conf'


def fetch_blocklist():
    resp = requests.get(blocklist_url)
    with open('src/saas/rules/blocklist.txt', 'w') as f:
        f.write(resp.text)


if __name__ == '__main__':
    fetch_blocklist()
