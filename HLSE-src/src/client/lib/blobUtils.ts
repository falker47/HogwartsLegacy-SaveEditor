function downloadURL(data, fileName) : void
{
    const hiddenDownloadLink = document.createElement('a');
    hiddenDownloadLink.href = data;
    hiddenDownloadLink.download = fileName;
    document.body.appendChild(hiddenDownloadLink);
    hiddenDownloadLink.style.display = 'none';
    hiddenDownloadLink.click();
    hiddenDownloadLink.remove();
}

export function downloadBlob(data, fileName, mimeType = 'application/octet-stream') : void
{
    const blob = new Blob([ data ], {
        type: mimeType
    });

    const url = URL.createObjectURL(blob);

    downloadURL(url, fileName);

    setTimeout(() => URL.revokeObjectURL(url), 1000);
}
