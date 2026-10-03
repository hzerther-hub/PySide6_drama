---
name: extractor
description: Standar dan metode ekstraksi karakter, latar, dan prop
---

# Panduan Ekstraksi Karakter, Latar, dan Prop

## Standar Ekstraksi Karakter

Field karakter hasil ekstraksi (berpasangan satu-satu dengan parameter tool `save_dedup_characters`):
- **name** (wajib): nama lengkap karakter
- **role**: posisi karakter — tokoh utama/tokoh pendukung/extra
- **appearance**: deskripsi penampilan (300-500 karakter) — gender, kesan usia, fitur wajah, postur tubuh, watak. **Ciri kepribadian karakter jangan dioutput secara terpisah; ubah menjadi watak luar dan ekspresi yang melebur ke dalam deskripsi penampilan** (misalnya "kepribadian dingin dan tegas" sebaiknya ditulis "tatapan mata dingin, ekspresi terkendali, jarang tersenyum")
- **styling**: tata rias dan busana — gaya rambut, pakaian, riasan wajah, aksesori, dsb.
- **description**: latar belakang cerita dan relasi antar karakter (pelengkap opsional)

## Standar Ekstraksi Latar

Field latar hasil ekstraksi (berpasangan satu-satu dengan parameter tool `save_dedup_scenes`):
- **location** (wajib): nama tempat yang spesifik
- **time**: rentang waktu (misalnya siang/senja/tengah malam); lokasi sama dengan rentang waktu berbeda dianggap latar baru
- **prompt**: deskripsi latar — ruang, tata letak barang, tekstur era, elemen visual kunci (murni latar belakang, tanpa tokoh)
- **lighting**: cahaya dan bayangan latar — sumber cahaya, corak warna, terang-gelap, suasana

## Standar Ekstraksi Prop

**Prinsip inti: lebih baik mengambil sedikit daripada terlalu banyak.** Prop adalah aset berbiaya tinggi yang dipakai untuk membuat gambar produk berlatar putih dan dirujuk untuk close-up video; hanya prop kunci yang menentukan alur cerita yang layak diekstraksi. Satu episode biasanya memiliki **0-3 prop** kunci; bila lebih dari 3, urutkan berdasarkan tingkat kepentingannya bagi alur cerita dan simpan hanya 3 teratas.

Kedua syarat berikut harus **dipenuhi sekaligus**, tidak boleh kurang salah satunya:
1. **Langsung menggerakkan alur cerita**: kemunculan, serah terima, kerusakan, atau penemuan benda tersebut memicu titik balik cerita (misalnya senjata pembunuh, benda kenang-kenangan, dokumen kunci, hadiah tanda cinta, bukti kunci).
2. **Layak dibuatkan gambar tersendiri**: storyboard berikutnya akan memberinya close-up atau benda itu muncul berulang kali, sehingga perlu penampilan yang tetap.

**Tiga pertanyaan penilaian** (ajukan dan jawab sendiri untuk setiap kandidat prop; jika ada satu saja yang terjawab "tidak", gugurkan):
- (1) Bila prop ini dihapus, apakah alur cerita tetap berdiri? → Bila tetap berdiri, **jangan diekstraksi** (prop itu hanyalah latar belakang pengamen)
- (2) Apakah ia sekadar benda sehari-hari yang dipakai karakter secara lalu-lalang (ponsel, sumpit, gelas air, rokok, payung)? → Bila ya, **jangan diekstraksi**
- (3) Apakah ia bagian dari tata letak latar (meja kursi, lampu, pintu jendela, lukisan gantung, alat makan)? → Bila ya, **jangan diekstraksi** (semua ini termasuk deskripsi latar)

**Yang secara tipikal tidak terhitung prop**: benda biasa yang dipakai lalu-lalang tanpa memengaruhi arah cerita; tata letak dan perabot latar; benda yang hanya disebut sekali dan tidak pernah muncul lagi; pakaian rutin karakter (masuk ke dalam styling karakter).

Bila tidak ada prop yang memenuhi syarat, **jangan memaksakan ekstraksi** — cukup kirimkan array kosong saat memanggil `save_dedup_props`.

Field prop hasil ekstraksi (berpasangan satu-satu dengan parameter tool `save_dedup_props`):
- **name** (wajib): nama prop
- **type**: kategori — sehari-hari/senjata/transportasi/dekorasi/dokumen, dsb.
- **description**: penampilan luar benda — hanya deskripsi penampilan fisik benda itu sendiri (material, warna, bentuk, ukuran, tingkat kebaruan, jejak keausan, dsb.), jangan menuliskan kegunaannya dalam cerita, jangan menyentuh kaitannya dengan karakter atau benda lain

Prop **tidak perlu dioutputkan prompt gambarnya** — prompt akhir prop dibuat khusus oleh Agent pembuat prompt sebelum pembuatan gambar (standar gambar produk berlatar putih).

## Langkah-Langkah Penggunaan

1. Panggil `read_script_for_extraction` untuk membaca naskah episode saat ini
2. Panggil `read_existing_characters` untuk melihat karakter yang sudah ada di proyek dan karakter yang sudah terhubung ke episode saat ini
3. Panggil `read_existing_scenes` untuk melihat latar yang sudah ada di proyek dan latar yang sudah terhubung ke episode saat ini
4. Panggil `read_existing_props` untuk melihat prop yang sudah ada di proyek dan prop yang sudah terhubung ke episode saat ini
5. Hanya ekstraksi karakter, latar, dan prop yang benar-benar terlibat dalam episode saat ini
6. Panggil `save_dedup_characters` untuk menyimpan karakter dan otomatis menghubungkannya ke episode saat ini
7. Panggil `save_dedup_scenes` untuk menyimpan latar dan otomatis menghubungkannya ke episode saat ini
8. Panggil `save_dedup_props` untuk menyimpan prop dan otomatis menghubungkannya ke episode saat ini

## Aturan Episode Saat Ini

- Tujuannya adalah melengkapi karakter, latar, dan prop yang dibutuhkan "episode saat ini", bukan memindai ulang seluruh proyek
- Bila sudah ada di proyek tetapi belum terhubung ke episode saat ini, tetap gunakan kembali dan hubungkan ke episode saat ini
- Aturan deduplikasi: karakter/prop dicocokkan tepat berdasarkan nama, latar dicocokkan tepat berdasarkan 【lokasi + rentang waktu】; bila cocok, utamakan penggunaan kembali, jangan membuat duplikat
- Deduplikasi nama mirip: bila nama membawa kualifikasi dalam kurung atau alias, bandingkan berdasarkan bagian utama sebelum tanda kurung (misalnya "Rani (tokoh utama)" dan "Rani" dianggap karakter/prop yang sama, gunakan kembali yang sudah ada); normalized_name yang dikembalikan oleh read_existing_characters / read_existing_props adalah nama yang sudah dinormalisasi, normalized_location untuk latar juga seterusnya — gunakan itu sebagai dasar penilaian
