import httpx
import time

base = 'http://localhost:8000'

def run_tests():
    print('1. Testing Health Endpoint...')
    r = httpx.get(f'{base}/api/health')
    assert r.status_code == 200, f'Health failed: {r.text}'
    print('   -> Health Response:', r.json())

    print('2. Testing Voice Catalog & Preview...')
    r = httpx.get(f'{base}/api/voices?language=en&style=Cinematic')
    assert r.status_code == 200, f'Voices failed: {r.text}'
    voices = r.json()
    assert len(voices) > 0, 'No voices returned'
    top_voice = voices[0]['voice']['voice_id']
    conf = voices[0]['confidence']
    print(f'   -> Top voice for English Cinematic: {top_voice} (Score: {conf})')

    r = httpx.post(f'{base}/api/voices/{top_voice}/preview')
    assert r.status_code == 200, f'Preview failed: {r.text}'
    assert len(r.content) > 1000, 'Preview audio content empty'
    print(f'   -> Preview audio received ({len(r.content)} bytes)')

    print('3. Testing Project Creation...')
    create_payload = {
        'text': 'The storm grew intense. The lighthouse beacon flickered in the dark.',
        'style_preference': 'Cinematic',
        'emotion_mode': 'suspense'
    }
    r = httpx.post(f'{base}/api/projects', json=create_payload)
    assert r.status_code == 200, f'Create project failed: {r.text}'
    project = r.json()
    proj_id = project['id']
    print(f'   -> Project Created: {proj_id}')

    print('4. Testing Voice Generation Pipeline...')
    gen_payload = {
        'text': create_payload['text'],
        'voice_id': 'auto',
        'style_preference': 'Cinematic',
        'emotion_mode': 'suspense',
        'enable_audio_mastering': True
    }
    start = time.time()
    r = httpx.post(f'{base}/api/projects/{proj_id}/generate', json=gen_payload, timeout=60.0)
    assert r.status_code == 200, f'Generation failed: {r.text}'
    gen_result = r.json()
    elapsed = time.time() - start
    print(f'   -> Generation Completed in {elapsed:.2f}s! Status: {gen_result["status"]}, Duration: {gen_result["total_duration_seconds"]}s')
    assert gen_result['status'] == 'COMPLETED'
    assert len(gen_result['chunks']) >= 2, f'Expected >= 2 chunks, got {len(gen_result["chunks"])}'

    print('5. Testing Audio Streaming (MP3 and WAV)...')
    r_mp3 = httpx.get(f'{base}/api/projects/{proj_id}/audio?format=mp3')
    assert r_mp3.status_code == 200, 'MP3 stream failed'
    assert len(r_mp3.content) > 10000, 'MP3 stream empty'
    print(f'   -> MP3 stream verified: {len(r_mp3.content)} bytes')

    r_wav = httpx.get(f'{base}/api/projects/{proj_id}/audio?format=wav')
    assert r_wav.status_code == 200, 'WAV stream failed'
    assert len(r_wav.content) > 20000, 'WAV stream empty'
    print(f'   -> WAV stream verified: {len(r_wav.content)} bytes')

    print('6. Testing Subtitles Download (SRT and VTT)...')
    r_srt = httpx.get(f'{base}/api/projects/{proj_id}/subtitles?format=srt')
    assert r_srt.status_code == 200, 'SRT failed'
    assert '-->' in r_srt.text, 'SRT format invalid'
    print('   -> SRT verified content:\n' + r_srt.text.strip())

    print('7. Testing Surgical Line-by-Line Redo (Chunk 1)...')
    r_redo = httpx.post(f'{base}/api/projects/{proj_id}/chunks/1/redo', timeout=30.0)
    assert r_redo.status_code == 200, f'Redo failed: {r_redo.text}'
    updated_proj = r_redo.json()
    print('   -> Redo Completed! Project updated successfully.')

    print('8. Testing Persistence Retrieval...')
    r_get = httpx.get(f'{base}/api/projects/{proj_id}')
    assert r_get.status_code == 200, 'Get project failed'
    retrieved = r_get.json()
    assert retrieved['id'] == proj_id, 'Project ID mismatch'
    print(f'   -> SQLite Persistence Verified for {proj_id}')

    print('\nALL LIVE HTTP INTEGRATION TESTS PASSED! [OK]')

if __name__ == '__main__':
    run_tests()
