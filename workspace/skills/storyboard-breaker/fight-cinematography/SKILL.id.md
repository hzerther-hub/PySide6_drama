---
name: fight-cinematography
description: Buku panduan gerakan kamera pertarungan kecepatan tinggi — rumus posisi kamera, anotasi kecepatan, dan cara penulisan prompt untuk segmen pertarungan/kejaran/titik ledak
---

# Buku Panduan Gerakan Kamera Pertarungan Kecepatan Tinggi (khusus segmen pertarungan/aksi kecepatan tinggi)

## Kapan Diaktifkan (penilaian otomatis)

Bila segmen atau sub-shot di dalam segmen memunculkan aksi kecepatan tinggi seperti **pertarungan, serbuan, kejaran, menghindar dan membalas, tendangan terbang, ledakan pukulan keras, terpental kena pukulan**, pilihlah gerakan kameranya dari 「Rumus Posisi Kamera」 dan 「Anotasi Kecepatan」 dalam buku panduan ini, diprioritaskan di atas kamus gerakan kamera dasar; segmen dialog, segmen pembangunan, dan segmen jembatan tidak memakai buku panduan ini.

Logika intinya hanya dua: **cepat** dan **antisipasi** — menciptakan kecepatan, memperbesar kecepatan. Gerakan kamera melayani tiga tujuan:
1. Membuat penonton melihat dengan jelas lintasan aksi
2. Memperkuat daya hantam arah serangan
3. Memakai kecepatan kamera untuk menciptakan rasa tertekan

## Rumus Posisi Kamera (10 rumus)

Setiap rumus ＝ kombinasi posisi kamera/gerakan ＋ jurus yang berlaku ＋ cara penulisan prompt (penulisannya dapat langsung disisipkan di awal 【镜头N】 milik `description`):

| # | Rumus | Jurus yang berlaku | Cara penulisan prompt |
|---|---|---|---|
| 1 | Tabrakan titik awal: posisi kamera rendah＋push-in kilat | Pukulan keras, serbuan, benturan pertama | Posisi kamera low-angle 0.5 meter, kamera push-in kilat dari bawah ke atas, menangkap debu yang beterbangan saat kedua pihak berbenturan berkecepatan tinggi serta kesan volumetris gelombang kejut, LOW angle memperkuat rasa tertekan |
| 2 | Tracking menyamping: kamera mengitari＋pergantian fokus | Combo, transisi serang-bertahan, serang balas dinamis | ORBIT mengitari membentuk setengah pengepungan dari belakang penyerang, fokus terkunci pada helaian rambut dan ujung pakaian pihak yang dipukul, fokus berpindah pada saat benturan |
| 3 | Mengikuti menempel tanah: sudut menempel tanah＋tracking posisi rendah | Sapuan kaki, berguling di tanah, aksi posisi rendah | Kamera low-angle menempel tanah mengikuti gerakan kaki menyapu, serpihan tanah melesat lewat di depan lensa |
| 4 | Mengejar di udara: low-angle mendongak＋tilt-up kilat | Tendangan terbang, tendangan berputar, combo tendangan di udara | Low-angle mendongak, TILT UP kilat mengikuti tubuh yang melayang, menekankan kesan melayang sesaat |
| 5 | Saat benturan: freeze mendadak＋getaran halus | Satu pukulan mengenai sasaran, titik ledak | Close-up saat benturan, gambar blur kecepatan tinggi 0.15 detik, bagian yang terkena meninggalkan bayangan sisa, kamera memantul bergetar halus |
| 6 | Terpental: pull-back kilat＋menguntit | Terpental kena pukulan keras, terdorong mundur | Kamera pull-back kilat, menguntit sepanjang arah jejak tubuh yang terpental, latar belakang terbelah ke dalam kedalaman |
| 7 | Sangat dekat: sudut tracking＋dorongan DOLLY | Pukulan berantai, serangan kombinasi | DOLLY dorongan horizontal, kamera sangat dekat dengan kedua pihak yang berkelahi, membuat penonton merasakan tekanan angin pukulan |
| 8 | Menghindar dan membalas: push-in terbalik＋pergantian fokus | Menghindar, bertahan lalu menyerang | Kamera push-in kilat dari belakang penyerang, PAN menyapu menyamping ke arah serangan balasan, PUSH push-in kilat ke aksi balasan, fokus berpindah sesaat dari penyerang ke penyerang balik |
| 9 | Balasan sudut atas: sudut mendongak＋pull-back kilat | Balasan dari bawah ke atas, serangan melayang | Low-angle mendongak sebagai pembuka, pull-back kilat mengikuti tubuh yang melayang, dari close-up sudut bawah terbentang sesaat menjadi wide shot udara |
| 10 | Freeze penutup jurus: push-in dekat perlahan＋mundur perlahan | Menutup jurus, pose perkenalan, menanam tenaga untuk pukulan berikutnya | MCU medium-close push-in perlahan membekukan pose karakter, kemudian PULL mundur perlahan meluruhkan latar, mempertahankan ketegangan sesaat sebelum jurus berikutnya meledak |

## Anotasi Kecepatan (4 jenis, ditumpukkan di atas rumus posisi kamera)

| Anotasi | Dipakai untuk | Efek | Penulisan |
|---|---|---|---|
| Swift kejaran cepat | Serbuan, menembus, menguntit, pergerakan jarak dekat | Rasa tegang, rasa kecepatan, ritme kuat | Medium shot push-pull kilat; elemen foreground melesat cepat, latar belakang menimbulkan motion blur horizontal |
| Whip whip pan | Berbalik, menghindar, saat benturan, perubahan arah mendadak | Kejutan mendadak, kesan meledak | WHIP menyapu pada saat menyentuh target, fokus langsung berpindah ke pihak yang terkena |
| Gentle mundur perlahan | Penindasan berakhir, debu berpipih, memperlihatkan medan pertempuran | Ketegangan setelah penutupan | Kamera mundur perlahan dari satu titik paling sengit konflik, fokus terkunci pada karakter, medan pertempuran di latar terbentang perlahan |
| Shock guncangan | Pukulan keras, ledakan, pecah, runtuh | Kejutan mendalam | Pada saat benturan kamera shake 0.3 detik, gambar bergetar halus, kerikil tanah terbelah sepanjang arah gelombang kejut |

## Aturan Penulisan (menghadapkan pada field storyboard)

- `movement`: pilih nama rumus atau kombinasinya dari tabel di atas (misalnya 「Mengejar di udara (low-angle mendongak＋tilt-up kilat)」), satu sub-shot satu gerakan kamera utama
- 【镜头N】 milik `description`: awal sub-shot menuliskan instruksi shot lengkap ＝ **posisi kamera/sudut ＋ cara gerakan ＋ keterangan kecepatan ＋ ukuran shot**; angka-angka (0.5 meter, 0.15 detik, 0.3 detik) dipertahankan apa adanya — video-prompt menguraikan segmen demi segmen berdasarkan description, kehilangan angka berarti kehilangan rasa kecepatan
- Kata keterangan kecepatan harus konkret: kilat/kecepatan stabil/perlahan/cepat lalu lambat; dilarang hanya menulis 「push-in」「tracking」
- Satu segmen satu gerakan kamera, kontinu di dalam segmen; segmen pertarungan diperbolehkan hard switch rumus antar sub-shot, titik ganti shot sejajar dengan 【镜头N】
- **Gabungan cepat-lambat**: setelah 2-3 sub-shot kilat berturut-turut, pakai satu Gentle mundur perlahan atau freeze saat benturan sebagai bantalan, baru masuk ledakan berikutnya; satu segmen penuh kecepatan kilat akan berubah jadi kabur semu, penuh lambat kehilangan rasa tertekan
- Bullet time/slow motion tetap termasuk trik aksen, patuhi batas 1-2 kali per episode pada standar dasar, hanya untuk saat benturan atau freeze penutup jurus

## Templat Serbaguna (pakai langsung)

- **Pembuka kecepatan tinggi**: rumus 1 (push-in kilat posisi rendah) ＋ Swift
- **Segmen combo**: rumus 7 (sangat dekat DOLLY) ↔ rumus 2 (ORBIT pergantian fokus), hard cut antar sub-shot
- **Menghindar dan membalas**: rumus 8 (push-in terbalik pergantian fokus) ＋ Whip
- **Ledakan pukulan keras**: rumus 5 (blur 0.15 detik saat benturan) ＋ Shock (shake 0.3 detik) → rumus 6 (pull-back kilat menyusuri jejak)
- **Freeze penutup jurus**: rumus 10 (MCU push-in perlahan → Gentle mundur perlahan), menanam tenaga untuk jurus berikutnya

## Ringkasan Satu Kalimat

Esensi gerakan kamera pertarungan adalah 「**selalu bergerak**」 — memakai gerakan kamera menyampaikan rasa kecepatan dan rasa tertekan kepada penonton, kecepatan kilat dan freeze sesaat berselang-seling, di sela-sela antar jurus menyelesaikan penanaman tenaga dan penyambungan.
