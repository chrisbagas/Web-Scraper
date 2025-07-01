from TikTokApi import TikTokApi
import asyncio
import os

ms_token = 'QOfiJChhl7clZ6xjxWHmPlZnDdNNXbjdRDc8wzJQzC4gzO3NN4ah4EfdjP4GNJdMdSkORrkp66Y77PCJ3KUIT1ES16g8GbPpa55di1Ypyk5iDoN5f-l0k9PVduGFczfPQmFueDyNMNER6im2h1me_j4='


async def get_video_example():
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser=os.getenv("TIKTOK_BROWSER", "chromium"))
        video = api.video(
            url="https://vt.tiktok.com/ZSkXFDfUE/"
        )
        video_info = await video.info()  # is HTML request, so avoid using this too much
        print(video_info)

if __name__ == "__main__":
    asyncio.run(get_video_example())
