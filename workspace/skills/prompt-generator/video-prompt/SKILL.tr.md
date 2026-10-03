---
name: video-prompt
description: Video prompt standardı — storyboard parçası içeriğinden zamana bölünmiş, parça içinde plan geçişine izin veren video üretim promptu oluşturma
---

# Video Promptu (storyboard parçası → video_prompt)

Tek bir storyboard parçasının description (içinde 【镜头N】 alt plan yapısı ile replik/anlatıcı metin) / atmosphere / duration alanlarından yola çıkarak, AI video üretimini süren `video_prompt` oluşturulur. **Bir storyboard parçası = 8-15 saniyelik bir video, içinde plan geçişi (kesme) serbesttir**: parçalar farklı planlar olabilir (plan ölçeği/açı/özne değişir), sert kesmeyle birleşir; ama **boydan boya sahne dışına çıkılmaz**, geriye dönüş (flashback) kullanılmaz.

## Biçim

`video_prompt`un **ilk satırı bilgi başlığıdır**: önce bu videoda hangi karakter ve sahnenin bulunduğu tanıtılır, ardından zaman bölümleri gelir. Karakterler ve sahneler her zaman @ ile referans verilir (üretim sırasında ilgili referans görsel işaretleriyle değiştirilir; video modeli önce "kim" ve "nerede"yi eşleştirir).

```
Karakterler: @Emre, @Zeynep; Sahne: @Kahve Dükkanı.
0-3 saniye: @Kahve Dükkanı, yakın plan, kamera nefes hissiyle hafifçe dalgalanarak @Emre'ye doğru yavaşça yaklaşıyor; o başını telefonuna eğmiş, parmakları masaya ritmik dokunuyor, ifadesi endişeli.
3-6 saniye: Kapıya genel plana kes; zil çalıyor, @Zeynep kapıyı iterek içeri giriyor, yanında bir soğuk esinti getiriyor.
6-9 saniye: Orta plana geri kes; @Zeynep gülümseyerek Emre'nin yanına gidip oturuyor, Emre der: "Nihayet geldin."
```

Bilgi başlığı kuralları:
- Yalnızca bu storyboard parçasında gerçekten yer alan karakterler ve bağlı sahne listelenir; görünmeyenler yazılmaz
- Belirgin bir öğe (prop) görünüyorsa bilgi başlığına eklenebilir (ör. `；Öğe: @Mektup`)
- Bilgi başlığı ayrı bir satırdır, nokta ile biter, ardından zaman bölümleri gelir

3 saniyelik bölümler hâlinde, her bölüm ayrı satırda ve satır sonlarıyla ayrılmış; zaman aralıkları kesintisiz birbirine eklenir (çakışma yok, boşluk yok).

## Storyboard Betimiyle Eşleme

`description`, video_prompt'un tek içerik kaynağıdır (görüntü, eylem, replik, anlatıcı metnin hepsi içindedir); dönüşüm kuralları:

- `description` içindeki her `【镜头N】`, **1-2 ardışık 3 saniyelik bölüme** eşlenir; sıra aynıdır, atlama yok, birleştirme yok, yeni alt plan eklenmez
- Replikler/anlatıcı metni, ilgili `【镜头N】` içindeki "KarakterAdı der: "…"" ve "Anlatıcı: …" kalıplarından çıkarılır ve bu alt planın eşlendiği bölümlere dağıtılır; **description dışında yeni replik üretilmez**
- Görüntü ve eylem `description`a göre yazılır; `atmosphere` yalnızca her bölümün ışık, renk tonu ve atmosfer betimini tamamlamak için kullanılır

## Bölüm İçi Yapı

Her bölümün içeriği bu sırayla düzenlenir (içeriği olmayan kalemler atlanabilir; ama eylem/görüntü zorunludur):

**Zaman aralığı ＋ sahne @referansı ＋ plan ölçeği/kamera hareketi ＋ karakter @referansı＋ana eylem·ifade ＋ diyalog/anlatıcı ＋ atmosfer-ışık**

- **İlk bölüm mekânı kurmak zorundadır**: sahne + kamera konumu + karakterlerin konumu ve durumu; seyirci bir bakışta nerede olduğunu ve kime bakması gerektiğini bilsin
- **Plan geçişi (kesme)**: kesme sonrası bölüm, "kes" / "geri kes" gibi bağlantı sözcüğüyle açılır ve plan ölçeği ile özne yeniden verilir; kesme noktaları storyboard `description`undaki `【镜头N】` yapısına hizalanır
- **Plan ölçeği/kamera hareketi (zorunlu kural)**: her bölümde hem **plan ölçeği** (yakın plan/orta plan/genel plan/yakın çekim) hem de **kamera hareketi yönergesi** açıkça yazılır; tek bir alt plan içinde kamera hareketi kesintisizdir, kesmeden sonra değişebilir. Yazım biçimi ＝ "başlangıç plan ölçeği ＋ hareket biçimi ＋ hız/ritim", ör. "orta plandan yüz yakın çekimine sabit hızla yavaş yaklaşma", "karakterle eş adımlı yanal kayma, arka planda paralaks akıyor". Tüm bölümü tek başına "sabit kamera" olarak yazmak yasaktır — kamera "hareketli" olmalıdır (yer değiştirme, zoom, takip, nefes dalgalanmasının hepsi sayılır); sunum slaytı (PPT) tarzı donuk karelerden kaçınılır. Kamera hareketi söz dağı için aşağıdaki "Kamera Hareketi Standardı"na bak
- **Eylem**: her bölümde bir ana eylem; fiiller somut ve gözlenebilir (yürümek, dönmek, başını kaldırmak, sıkmak, duraklamak)
- **Duygunun tamamı görünür betime dönüştürülür**: "çok üzgün/hava gergin" türü soyut sözcükler yok; "başını öne eğiyor, parmakları bardağın ağzını sıkıyor, nefesi ağırlaşıyor" biçiminde yazılır
- **Diyalog/anlatıcı**: "KarakterAdı der: "replik"" yazılır, anlatıcı metni "Anlatıcı: içerik" yazılır; 3 saniyede bitmeyecek uzun replikler birden çok bölüme dağıtılır; diyaloğun olmadığı bölümlerde ortam sesi/eylem sesi yazılabilir (ör. "makinalar durmaksızın uğulduyor")

## Referans Kuralları

- `@SahneAdı` — sahne referansı; ad, sahne listesindeki mekânla tam olarak aynı olmalıdır
- `@KarakterAdı` — karakter referansı; ad, karakter listesindeki adla tam olarak aynı olmalıdır
- `@ÖğeAdı` — öğe referansı; ad, öğe listesindeki adla tam olarak aynı olmalıdır; öğe karede belirgin görünürken, kullanılırken ya da yakın çekimde verilirken referans verilir
- Üretim sırasında her `@ad` ilgili referans görsel işaretiyle otomatik değiştirilir (ör. `@Emre` → `@Resim1Emre`); bu yüzden adlar tam eşleşmelidir, kısaltma ve fazladan simge eklenmez
- **Her bölümde kareyi sabitleyen en az bir @ referansı bulunur**; karakterin göründüğü bölüm o karakteri @ ile anar; yalnızca bu storyboard parçasına bağlı sahne/karakter/öğelere referans verilir

## Zaman Çizelgesi Kuralları

- Bölüm sayısı ＝ storyboard parçasının duration ÷ 3 saniye (yukarı yuvarlanır); bölümlerin zaman aralıkları toplandığında parçanın toplam süresine tam olarak eşit olmalıdır
- İçerik ritmi: ilk bölüm kurar → orta bölümler eylemi/çatışmayı ilerletir → son bölüm sonuçta ya da duygu noktasında konar

## Kamera Hareketi Standardı

Her zaman aralığında bir kamera hareketi bulunur; aşağıdaki söz dağından seçilir ve storyboard `description`/`movement` alanındaki kamera niyetiyle tutarlıdır (description hangi kamera hareketini yazdıysa video_prompt onu açar; description yazmadıysa görüntü içeriğine en uygun olanı kendin seç):

- **Temel anlatım**: yavaş yaklaşma (orta plan→yakın çekim, sabit hız, arka plan giderek flu), uzaklaşarak açığa çıkarma (yakın çekim→genel plan, önce hızlı sonra yavaş), yanal takip (özneyle eş adım hareket, arka planda paralaks akışı), yükselme-alçalma ile kuşbakışı (dikey yükselme/alçalma ile mekânın gösterimi), yay dolanma (karakter merkezli 90-180 derece dolanma), birinci şahıs yürüyüş (göz hizası, nefes gibi hafif dalgalanma)
- **Duygu ve atmosfer**: elde tutma sarsıntısı (hafif titreme, hareket sonrası artar), gözetleme açısı (kapı aralığı/pencere boşluğu ön plan örtüsü), kalp atışı nabzı (yaklaşma-uzaklaşma duygu ritmiyle eş zamanlı, sakin pasajda yavaş yaklaşma/gerilimde hızlı yaklaşma), nefes uyumu (iç çekerken hafif yaklaşma, verirken yavaş uzaklaşma)
- **Psikoloji ve ayrıntı**: bakış odağı (bakılan nesneye yavaşça yaklaşma, odak değişimi), ürperti titremesi (düzensiz ince titreme), yumuşak dolanma (yavaş, küçük açılı dolanma; odak yüzde kilitli), yüksek hızlı kuyruklama (hareketli hedefe yapışık takip, hareket bulanıklığı), dövüş arası geçiş (kapışan iki taraf arasında hızlı kesmeler), dalış inişi (yüksekten dalış, yere değmede hafif sarsıntı)
- **Yüksek hızlı dövüş**: yalnızca storyboard `description` açıkça dövüş kamera hareketi yazdığında, description aynen açılır (kamera konumu, hız, sayılardan tek biri bile eksik olamaz): alçak konumdan ani hızlı yaklaşma, yere yapışık takip, ani hızlı yukarı savırma (TILT UP), azami yakınlıkta takip, ters yönlü yaklaşma ile odak değişimi, ani hızlı uzaklaşma ve iz sürme, isabet anında 0.15 saniye yüksek hızlı bulanıklaştırma, ağır vuruşta 0.3 saniye shake
- **Özel açılar**: aşırı alçak açıdan çekim, Hollanda açısı (eğik kadraj), omuz üstü yakın plan, öznel bakış (POV)
- **Ritim geçişleri**: hızlı savurma (savurma yönü bir sonraki bölümün hareket yönüyle aynı), örtü geçişi (ön plan nesnesi gözü kapattığı anda kesme), ani duruş ve dondurma (yavaşlayıp durağan kareye oturma; yalnızca patlama bölümlerinde)

Yazım koşulları:
- Kamera hareketi yönergesi plan ölçeği ve hızla birlikte verilir: "genel plandan orta plana yavaşça yaklaşma"; yalnızca "yaklaşma" yazmak yok
- Hız zarfları somuttur: sabit hız / yavaş / ani hızlı / önce hızlı sonra yavaş / yavaşten hızlıya
- Bir bölümde bir kamera hareketi; bölüm içinde kesintisiz, yalnızca kesme noktasında değişir
- Bullet time / ağır çekim yakın çekim / balık gözü / minyatür maket, vurgu numaralarıdır; yalnızca storyboard `description` açıkça yazdığında kullanılır, bölüm başına en fazla 1-2 kez
- Elde tutma sarsıntısı ve nefes dalgalanması "mikro hareket" sayılır; sabit kamera yazılmak istenen bölümlerde, tamamen durgunluğun yerine kullanılabilir

## Yasaklar

- Sahneler arası geçiş, geriye dönüş (bir bölüm tek bir sahnenin içinde geçer)
- Listeler dışındaki sahne/karakter adlarına referans
- Soyut psikolojik betimleme, edebi benzetmeler (model yalnızca görünür görüntüyü tanır)
- Aşırı oyunculuk: çığlık, haykırma, bağırış çağırış, gülüp ağlama yazılmaz; korku, mikro tepki olarak yazılır (donakalma, gözbebeklerinin büzülmesi, hıçkırık gibi nefes alma, yarım adım geri çekilme); diyaloglar gündelik ton ve gündelik ses düzeyiyle verilir (aşırı olay örgüsü gerçekten patlama gerektiriyorsa, ilgili bölümde açıkça "duygusal patlama" yazılarak geçilir)
- Ağır çekim ve durgunlukla oyalama: varsayılan olarak ağır çekim kullanılmaz, uzun süreli durgun bakış yazılmaz; istisna: storyboard `description` açıkça bullet time/ağır çekim yakın çekim/ani duruş dondurma yazmış patlama alt planları, description'a göre kullanılabilir. Yine de her bölümde görünür bir kamera hareketi ya da eylem ilerlemesi bulunmalıdır; "salt durgun plan"a izin yoktur
- Dilin oturum dil yönergesiyle uyuşmaması

## Kaydetme

`update_storyboard` çağırarak yalnızca bu storyboard parçasının `video_prompt` alanını güncelle; başka hiçbir alana dokunma, tüm bölümü yeniden bölmeye kalkma. Platform, gerçek üretim isteği sırasında oyunculuk ve tempo koruyucularını otomatik ekler; bu koşulların prompt içinde yeniden yazılmasına gerek yoktur.
