export async function openJobUrls(
  urls: string[],
  onBlocked?: (remaining: number) => Promise<boolean>
): Promise<void> {
  const batchSize = 5;
  for (let i = 0; i < urls.length; i += batchSize) {
    const batch = urls.slice(i, i + batchSize);
    let blocked = false;
    for (const url of batch) {
      const w = window.open(url, "_blank");
      if (!w) blocked = true;
    }
    if (blocked && onBlocked && i + batchSize < urls.length) {
      const remaining = urls.length - i - batchSize;
      const cont = await onBlocked(remaining);
      if (!cont) break;
    }
  }
}
