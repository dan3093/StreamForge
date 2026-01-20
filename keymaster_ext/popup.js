const btn = document.getElementById('btn');
const status = document.createElement('p');
status.style.cssText = 'font-size:10px; margin-top:10px;';
btn.parentNode.insertBefore(status, btn.nextSibling.nextSibling);

// Generate SAPISIDHASH from SAPISID cookie
async function generateSapisidHash(sapisid, origin) {
    const timestamp = Math.floor(Date.now() / 1000);
    const dataStr = `${timestamp} ${sapisid} ${origin}`;

    // SHA-1 hash
    const encoder = new TextEncoder();
    const data = encoder.encode(dataStr);
    const hashBuffer = await crypto.subtle.digest('SHA-1', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

    return `SAPISIDHASH ${timestamp}_${hashHex}`;
}

btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.textContent = 'EXTRACTING...';
    status.style.color = '#ff0';
    status.textContent = 'Grabbing cookies...';

    const url = 'https://music.youtube.com';
    const origin = 'https://music.youtube.com';

    try {
        const cookies = await chrome.cookies.getAll({ url: url });
        console.log('Cookies found:', cookies.length, cookies.map(c => c.name));

        if (cookies.length === 0) {
            // Try with domain instead
            const domainCookies = await chrome.cookies.getAll({ domain: '.youtube.com' });
            console.log('Domain cookies found:', domainCookies.length);
            if (domainCookies.length > 0) {
                cookies.push(...domainCookies);
            }
        }

        if (cookies.length === 0) {
            status.style.color = '#f00';
            status.textContent = '❌ No cookies found! Make sure you are logged into YouTube Music.';
            btn.textContent = 'RETRY';
            btn.disabled = false;
            return;
        }

        const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join('; ');
        console.log('Cookie string length:', cookieStr.length);

        // Find SAPISID cookie for auth hash
        const sapisidCookie = cookies.find(c => c.name === 'SAPISID');
        let authorization = '';

        if (sapisidCookie) {
            console.log('SAPISID found, generating hash...');
            status.textContent = 'Generating auth hash...';
            authorization = await generateSapisidHash(sapisidCookie.value, origin);
            console.log('Authorization:', authorization.substring(0, 30) + '...');
        } else {
            console.log('SAPISID not found in cookies:', cookies.map(c => c.name));
        }

        // Build headers in lowercase format (ytmusicapi requirement)
        const headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": authorization,
            "content-type": "application/json",
            "cookie": cookieStr,
            "origin": origin,
            "user-agent": navigator.userAgent,
            "x-goog-authuser": "0",
            "x-origin": origin
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
        a.download = 'streamforge_auth.json';
        a.click();

        setTimeout(() => {
            status.style.color = '#0f0';
            status.textContent = '✅ Downloaded! StreamForge will auto-import.';
            btn.textContent = 'KEYS EXTRACTED';
            btn.style.background = '#0f0';
        }, 500);
    } catch (err) {
        console.error('Error:', err);
        status.style.color = '#f00';
        status.textContent = '❌ Error: ' + err.message;
        btn.textContent = 'RETRY';
        btn.disabled = false;
    }
});
