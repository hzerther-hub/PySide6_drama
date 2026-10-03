---
name: video-prompt
description: Standar prompt video — menghasilkan prompt pembuatan video yang terbagi per rentang waktu berdasarkan isi segmen storyboard, dengan izin ganti shot di dalam segmen
---

# Prompt Video (segmen storyboard → video_prompt)

Berdasarkan description sebuah segmen storyboard (termasuk struktur sub-shot 【镜头N】 beserta dialog/narasi) / atmosphere / duration, hasilkan `video_prompt` yang menggerakkan pembuatan video AI. **Satu segmen storyboard = satu video berdurasi 8-15 detik, di dalamnya diperbolehkan ganti shot**: antar segmen boleh berupa shot berbeda (ganti ukuran shot/sudut/objek), disambung dengan hard cut; tetapi **sepanjang segmen tidak berpindah adegan** dan tanpa flashback.

## Format

**Baris pertama `video_prompt` adalah kepala informasi**: perkenalkan lebih dulu tokoh dan latar apa saja yang muncul di video ini, baru kemudian lanjut ke pembagian rentang waktu. Tokoh dan latar selalu dirujuk dengan @ (saat pembuatan, akan digantikan dengan penanda gambar referensi terkait, agar model video lebih dulu mencocokkan "siapa" dan "di mana").

```
Tokoh yang tampil: @Budi, @Siti; Latar: @Kafe.
0-3 detik: @Kafe, close shot, kamera berdenyut halus seperti napas dan perlahan push-in ke arah @Budi, ia menunduk menatap ponsel, jarinya mengetuk-ngetuk meja berulang kali, ekspresi cemas.
3-6 detik: Cut ke wide shot pintu masuk, bel pintu berbunyi, @Siti mendorong pintu dan masuk, membawa hembusan angin dingin.
6-9 detik: Cut kembali ke medium shot, @Siti berjalan sambil tersenyum mendekati Budi lalu duduk, Budi berkata: "Kau akhirnya datang."
```

Aturan kepala informasi:
- Hanya cantumkan tokoh yang benar-benar tampil di segmen storyboard ini dan latar yang terikat padanya, jangan mencantumkan yang tidak tampil
- Bila ada prop yang tampak mencolok, boleh ditambahkan ke kepala informasi (misalnya `; Prop: @Surat`)
- Kepala informasi berdiri pada baris sendiri, diakhiri titik, setelahnya barulah pembagian rentang waktu

Bagi per 3 detik satu segmen, setiap segmen pada baris tersendiri dan dipisahkan baris baru, rentang waktunya tersambung kontinu (tanpa tumpang tindih, tanpa celah).

## Pemetaan dengan Deskripsi Storyboard

`description` adalah satu-satunya sumber konten video_prompt (visual, aksi, dialog, narasi semuanya ada di dalamnya), aturan konversinya:

- Setiap `【镜头N】` pada `description` dipetakan menjadi **1-2 segmen 3 detik yang berurutan**, urutannya sama, tanpa ada yang terlewat, tanpa digabung, tanpa menambah sub-shot baru
- Dialog/narasi diambil dari 「nama karakter berkata: "..."」「Narasi: ...」 di dalam `【镜头N】` terkait, dialokasikan ke segmen hasil pemetaan sub-shot tersebut; **jangan menciptakan dialog baru di luar description**
- Aksi visual mengacu pada `description`; `atmosphere` hanya dipakai untuk melengkapi deskripsi cahaya, corak warna, dan suasana tiap segmen

## Struktur di Dalam Segmen

Setiap segmen disusun mengikuti urutan ini (butir tanpa isi boleh dilewati, tetapi aksi/visual wajib ada):

**Rentang waktu ＋ rujukan @ latar ＋ ukuran shot/gerakan kamera ＋ rujukan @ karakter＋aksi utama·ekspresi ＋ dialog/narasi ＋ suasana cahaya**

- **Segmen pertama wajib membangun ruang**: latar + posisi kamera + posisi dan keadaan karakter, agar penonton langsung tahu di mana dan menonton siapa
- **Ganti shot**: awal segmen setelah ganti shot memakai kata penghubung seperti "cut ke/cut kembali", lalu tegaskan kembali ukuran shot dan objeknya; titik ganti shot harus sejajar dengan struktur `【镜头N】` dalam `description` storyboard
- **Ukuran shot/gerakan kamera (aturan mutlak)**: setiap segmen wajib menuliskan **ukuran shot** (close shot/medium shot/wide shot/close-up) dan **instruksi gerakan kamera** sekaligus; di dalam satu sub-shot gerakan kamera kontinu, setelah ganti shot boleh mengganti cara gerakan kamera. Penulisannya ＝ "ukuran shot awal ＋ cara gerakan ＋ kecepatan/ritme", misalnya "medium shot push-in perlahan berkecepatan stabil hingga close-up wajah", "tracking menyamping serentak dengan karakter, latar mengalir dengan efek paralaks". Dilarang menulis satu segmen penuh hanya "kamera statis" tanpa informasi gerakan — kamera harus "bergerak" (perpindahan posisi, zoom, mengikuti, denyut seperti napas semuanya terhitung) untuk menghindari gambar bebas ala slide presentasi. Kamus gerakan kamera lihat "Standar Gerakan Kamera" di bawah
- **Aksi**: satu aksi utama per segmen, kata kerjanya konkret dan terlihat (berjalan, berbalik, mendongak, mengepalkan, berhenti sejenak)
- **Emosi seluruhnya diubah menjadi deskripsi yang terlihat**: jangan memakai kata abstrak seperti "ia sangat sedih/suasananya tegang", tuliskan sebagai "ia menunduk, jarinya mengepal rapat di bibir gelas, napasnya membesar"
- **Dialog/narasi**: dialog ditulis "nama karakter berkata: "kalimat"", narasi ditulis "Narasi: isi"; dialog panjang yang tak selesai dibaca dalam 3 detik dipecah ke beberapa segmen; segmen tanpa dialog boleh menuliskan suara lingkungan/suara aksi (misalnya "mesin mengamuk tanpa henti")

## Aturan Rujukan

- `@NamaLatar` — rujukan latar, namanya harus persis sama dengan lokasi dalam daftar latar
- `@NamaKarakter` — rujukan karakter, namanya harus persis sama dengan nama dalam daftar karakter
- `@NamaProp` — rujukan prop, namanya harus persis sama dengan nama dalam daftar prop; rujukkan prop bila tampak jelas di frame, sedang dipakai, atau mendapat close-up
- Saat pembuatan, `@nama` otomatis digantikan penanda gambar referensi terkait (misalnya `@Budi` → `@Gambar1Budi`), karena itu namanya harus cocok persis, jangan disingkat atau diberi simbol tambahan
- **Setiap segmen minimal satu rujukan @ untuk menjangkar gambar**; segmen tempat karakter tampil harus @ karakter itu; hanya rujukkan latar/karakter/prop yang sudah terikat pada segmen storyboard ini

## Aturan Garis Waktu

- Jumlah segmen ＝ duration segmen storyboard ÷ 3 detik (dibulatkan ke atas), penjumlahan rentang waktu semua segmen harus sama dengan total durasi segmen
- Ritme isi: segmen pertama membangun ruang → segmen tengah menggerakkan aksi/konflik → segmen akhir mendarat pada hasil atau titik emosi

## Standar Gerakan Kamera

Setiap rentang waktu harus memiliki gerakan kamera, dipilih dari kamus di bawah dan konsisten dengan niat gerakan kamera pada field `description`/`movement` storyboard (description menulis gerakan kamera apa, video_prompt menguraikan gerakan kamera itu; bila description tidak menuliskannya, pilih sendiri yang paling sesuai dengan isi gambar):

- **Naratif dasar**: push-in perlahan (medium shot → close-up, kecepatan stabil, latar perlahan blur), pull-back yang mengungkap (close-up → wide shot, cepat lalu melambat), tracking menyamping (bergerak serentak dengan karakter, latar mengalir dengan efek paralaks), crane naik/turun (naik/turun vertikal memperlihatkan ruang), orbit melengkung (mengitari karakter sebagai pusat 90-180 derajat), jalan sudut orang pertama (setinggi garis pandang, berdenyut halus seperti napas)
- **Suasana emosi**: napas handheld (goyangan halus, menguat setelah gerakan), sudut mengintip (celah pintu/jendela menghalangi foreground), denyut jantung (push-pull serentak dengan ritme emosi, tenang push-in perlahan/tegang push-in cepat), serupa napas (push-in tipis saat menarik napas, pull-back perlahan saat menghembuskan)
- **Detail psikologis**: fokus tatapan (push-in perlahan ke objek yang ditatap, perpindahan fokus), gemetar ketakutan (getaran halus tak beraturan), orbit lembut (orbit sudut kecil berkecepatan lambat, fokus terkunci di wajah), kejaran kilat (mengejar target yang bergerak dengan erat, motion blur), weave pertarungan (berpindah cepat di antara kedua pihak yang bertarung), menukik dari udara (menukik dari ketinggian, guncangan halus saat mendarat)
- **Pertarungan kecepatan tinggi**: hanya bila `description` storyboard secara eksplisit menuliskan gerakan kamera pertarungan, uraikan sesuai aslinya (posisi kamera, kecepatan, angka tidak boleh ada yang hilang): push-in kilat dari posisi rendah, mengikuti menempel tanah, tilt-up kilat, tracking sangat dekat, push-in terbalik dengan perpindahan fokus, pull-back kilat menyusuri jejak, blur kecepatan tinggi 0.15 detik pada saat benturan, shake guncangan 0.3 detik
- **Sudut istimewa**: low-angle ekstrem, kemiringan Dutch angle, over-the-shoulder dekat, sudut pandang orang pertama
- **Transisi ritme**: whip pan kilat (arah cambukannya sama dengan arah gerakan segmen berikutnya), transisi oklusi (benda foreground menyapu menghalangi sesaat lalu ganti shot), rem mendadak freeze frame (melambat hingga diam membeku, hanya untuk segmen titik ledak)

Persyaratan penulisan:
- Instruksi gerakan kamera selalu muncul terikat dengan ukuran shot dan kecepatan: "push-in perlahan dari wide shot hingga medium shot", jangan hanya menulis "push-in"
- Kata keterangan kecepatan harus konkret: kecepatan stabil/perlahan/kilat/cepat lalu lambat/lambat lalu cepat
- Satu segmen satu gerakan kamera; gerakan kontinu di dalam segmen, hanya berganti pada titik ganti shot
- Bullet time/close-up slow motion/fisheye/diorama miniatur adalah trik aksen, hanya dipakai bila `description` storyboard secara eksplisit menuliskannya, maksimal 1-2 kali per episode
- Goyangan handheld dan denyut napas termasuk "mikro-gerakan", dapat dipakai pada segmen yang tadinya ingin ditulis statis, menggantikan diam total

## Larangan

- Pindah adegan, flashback (satu segmen hanya berlangsung di satu adegan)
- Merujuk nama latar/karakter di luar daftar
- Deskripsi psikologis abstrak, kiasan sastra (model hanya mengenali gambar yang terlihat)
- Akting berlebihan: jangan menulis berteriak, mengaum, bersuara keras, menangis histeria; kejutan ditulis sebagai mikro-reaksi (membeku sebentar, pupil mengecil, menarik napas, mundur setengah langkah), dialog memakai nada sehari-hari dan volume sehari-hari (bila alur ekstrem memang memerlukan ledakan, tuliskan eksplisit "ledakan emosi" pada segmen tersebut untuk menimpanya)
- Slow motion dan diam yang bertele-tele: secara default tidak memakai slow motion, tidak menulis tatapan diam lama; pengecualian: sub-shot titik ledak yang `description` storyboard secara eksplisit menuliskan bullet time/close-up slow motion/rem mendadak freeze frame, boleh dipakai sesuai description. Setiap segmen tetap harus memiliki gerakan kamera yang terlihat atau kemajuan aksi, "shot murni statis" tidak diperbolehkan
- Bahasa tidak sesuai instruksi bahasa sesi

## Penyimpanan

Panggil `update_storyboard` untuk hanya memperbarui field `video_prompt` segmen storyboard tersebut, jangan mengubah field lain, jangan memecah ulang seluruh episode. Platform otomatis menambahkan penjaga akting dan ritme saat permintaan pembuatan aktual, persyaratan-persyaratan ini tidak perlu ditulis ulang di dalam prompt.
