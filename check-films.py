import json

data = json.load(open('films.json'))
real = 0
stubs = 0

for f in data['films']:
    has_yt = f.get('signals', {}).get('youtube_views') not in [None, 0]
    has_d1 = f.get('outcome', {}).get('day1_national_adm') is not None
    if has_yt or has_d1:
        real += 1
    else:
        stubs += 1
        print(f"STUB: {f['title']}")

print(f"\nReal: {real}, Stubs: {stubs}, Total: {real + stubs}")
