import argparse
from TikTokApi import TikTokApi
import pandas as pd
import asyncio
import os
import sys
import logging

# Suppress TikTokApi logger
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)

# Replace this with your actual TikTok ms_token string
ms_token = 'YOUR_MS_TOKEN_HERE'


async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()

        if "author" not in info or "authorStats" not in info or "stats" not in info:
            raise ValueError("Missing author or stats data")

        return {
            "video_url": url,
            "author_id": info["author"]["id"],
            "unique_id": info["author"]["uniqueId"],
            "nickname": info["author"]["nickname"],
            "music_title": info.get("music", {}).get("title"),
            "play_url": info.get("video", {}).get("playAddr"),
            "author_name": info.get("music", {}).get("authorName"),
            "hashtags": ", ".join(
                [h["hashtagName"]
                    for h in info.get("textExtra", []) if h.get("hashtagName")]
            ),
            "follower_count": int(info.get("authorStats", {}).get("followerCount", 0)),
            "heart_count": int(info.get("authorStats", {}).get("heart", 0)),
            "video_count": int(info.get("authorStats", {}).get("videoCount", 0)),
            "comment_count": int(info.get("stats", {}).get("commentCount", 0)),
            "play_count": int(info.get("stats", {}).get("playCount", 0)),
            "collect_count": int(info.get("statsV2", {}).get("collectCount", 0)),
            "share_count": int(info.get("stats", {}).get("shareCount", 0)),
            "repost_count": int(info.get("statsV2", {}).get("repostCount", 0)),
        }
    except Exception as e:
        print(f"❌ Failed to fetch info for {url} | Error: {e}")
        return {"video_url": url, "error": str(e)}


async def main(input_file):
    # Load Excel input
    try:
        df_urls = pd.read_excel('./input/'+input_file)
    except Exception as e:
        print(f"❌ Failed to read Excel file '{input_file}': {e}")
        sys.exit(1)

    if "video_url" not in df_urls.columns:
        print("❌ Excel file must contain a column named 'video_url'")
        sys.exit(1)

    video_urls = df_urls["video_url"].dropna().tolist()
    os.makedirs("output", exist_ok=True)
    output_file = os.path.join(
        "output", f"scraped_{os.path.splitext(os.path.basename(input_file))[0]}.xlsx")

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[ms_token],
            num_sessions=1,
            sleep_after=3,
            browser=os.getenv("TIKTOK_BROWSER", "chromium")
        )

        results = []
        failed = []

        for idx, url in enumerate(video_urls, 1):
            print(f"[{idx}/{len(video_urls)}] Scraping: {url}")
            data = await get_video_info(url, api)
            if data and "error" not in data:
                results.append(data)
            else:
                failed.append({
                    "video_url": url,
                    "error": data.get("error", "Unknown error") if data else "Unknown error"
                })

        # Save results to Excel
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            if results:
                pd.DataFrame(results).to_excel(
                    writer, index=False, sheet_name="Success")
            if failed:
                pd.DataFrame(failed).to_excel(
                    writer, index=False, sheet_name="Failed")

        print(f"\n✅ Scraping complete. Results saved to: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape TikTok video info from a list of URLs in Excel.")
    parser.add_argument(
        "input_file", help="Path to Excel file containing a column named 'video_url'")
    args = parser.parse_args()

    asyncio.run(main(args.input_file))
