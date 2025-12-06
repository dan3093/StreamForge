const btn = document.getElementById('btn');
const status = document.createElement('p');
status.style.cssText = 'font-size:10px; margin-top:10px;';
btn.parentNode.insertBefore(status, btn.nextSibling.nextSibling);

btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.textContent = 'EXTRACTING...';
    status.style.color = '#ff0';
    status.textContent = 'Grabbing cookies...';

    const url = 'https://music.youtube.com';
    const cookies = await chrome.cookies.getAll({ url: url });
    const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join('; ');

    // Build headers in lowercase format (ytmusicapi requirement)
    const headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "",  // Will be populated if we can intercept a request
        "content-type": "application/json",
        "cookie": cookieStr,
        "origin": url,
        "user-agent": navigator.userAgent,
        "x-goog-authuser": "0",
        "x-origin": url
    };

    // Try native messaging first (direct save to secure location)
    try {
        status.textContent = 'Saving to secure location...';
        const response = await chrome.runtime.sendNativeMessage(
            'com.streamforge.keymaster',
            { action: 'save_auth', headers: headers }
        );

        if (response && response.success) {
            status.style.color = '#0f0';
            status.textContent = '✅ Saved to: ~/.streamforge/';
            btn.textContent = 'KEYS EXTRACTED';
            btn.style.background = '#0f0';
            return;
        }
    } catch (e) {
        console.log('Native messaging not available, falling back to download');
    }

    // Fallback: download file
    status.textContent = 'Downloading (save to Downloads)...';
    const blob = new Blob([JSON.stringify(headers, null, 2)], { type: 'application/json' });
    const dlUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = dlUrl;
    a.download = 'browser.json';
    a.click();

    setTimeout(() => {
        status.style.color = '#0f0';
        status.textContent = '✅ Downloaded! StreamForge will auto-import.';
        btn.textContent = 'KEYS EXTRACTED';
        btn.style.background = '#0f0';
    }, 500);
});
