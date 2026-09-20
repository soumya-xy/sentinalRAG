import os
from supabase import create_client

url = 'https://clxhyzxzvniwnhdmwjye.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNseGh5enh6dm5pd25oZG13anllIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4OTQ3ODU3NCwiZXhwIjoyMTA1MDU0NTc0fQ.YATNeJ2k-JWYw61UcTXugjkhM9k8vN9pse4mN8JbQwY'

client = create_client(url, key)

res = client.table('events').select('event_id, video_id, user_id, camera_id, caption, embedding').limit(5).execute()
print(f"Total events returned: {len(res.data)}")
for row in res.data:
    emb = row.get('embedding')
    emb_len = len(emb) if emb else 0
    print(f"Event ID: {row['event_id']}, Video ID: {row['video_id']}, Embedding Dim: {emb_len}")

if res.data:
    video_id = res.data[0]['video_id']
    emb = res.data[0]['embedding']
    if emb:
        print(f"\nTesting match_events RPC with video_id={video_id}...")
        rpc_res = client.rpc('match_events', {
            'query_embedding': emb,
            'filter_video_id': video_id,
            'match_count': 5
        }).execute()
        print("RPC match_events result:", rpc_res.data)
