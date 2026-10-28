from helpers import Emoji, Tools, animate_proses


async def cuaca_cmd(client, message):
    em = Emoji(client)
    await em.get()
    prs = await animate_proses(message, em.proses)
    prompt = client.get_text(message)
    if not prompt:
        return await prs.edit(
            f"{em.gagal}**Please provide a location!\nExample: `{message.text.split()[0]} jakarta`**"
        )

    url = f"https://nolimitdev.cloud/api/tools/cuaca?lokasi={prompt}"
    respon = await Tools.fetch.get(url)

    if respon.status_code != 200:
        return await prs.edit(
            f"{em.gagal}**Failed to fetch weather data! Status code: {respon.status_code}**"
        )

    data = respon.json().get("result")
    try:
        current = data["current_condition"][0]
        area = data["nearest_area"][0]
        astronomy = data["weather"][0]["astronomy"][0]

        lokasi = area["areaName"][0]["value"]
        negara = area["country"][0]["value"]
        suhu = current["temp_C"]
        terasa = current["FeelsLikeC"]
        deskripsi = current["weatherDesc"][0]["value"]
        kelembaban = current["humidity"]
        angin = f"{current['winddir16Point']} ({current['windspeedKmph']} km/h)"
        tekanan = current["pressure"]
        uv = current["uvIndex"]
        visibilitas = current["visibility"]
        langit = current["cloudcover"]

        matahari_terbit = astronomy["sunrise"]
        matahari_terbenam = astronomy["sunset"]
        tanggal = data["weather"][0]["date"]
        waktu_lokal = current["localObsDateTime"]
        text = (
            f"🌤️ **Cuaca Saat Ini**\n\n"
            f"📍 Lokasi: `{lokasi}, {negara}`\n"
            f"🗓️ Tanggal: `{tanggal}`\n"
            f"🕒 Waktu Observasi: `{waktu_lokal}`\n"
            f"🌡️ Suhu: `{suhu}°C`, Terasa seperti: `{terasa}°C`\n"
            f"💧 Kelembaban: `{kelembaban}%`\n"
            f"☁️ Kondisi: `{deskripsi}`\n"
            f"🌬️ Angin: `{angin}`\n"
            f"🌫️ Visibilitas: `{visibilitas} km`, Awan: `{langit}%`\n"
            f"📈 Tekanan Udara: `{tekanan} mb`\n"
            f"🔆 Indeks UV: `{uv}`\n"
            f"🌅 Terbit: `{matahari_terbit}`\n"
            f"🌇 Terbenam: `{matahari_terbenam}`"
        )

        await message.reply(text)
    except Exception as e:
        await message.reply(f"{em.gagal}**ERROR:** `{str(e)}`")
    return await prs.delete()
