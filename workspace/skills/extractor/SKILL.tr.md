---
name: extractor
description: Karakter, sahne ve öğe (prop) çıkarımı için kurallar ve yöntemler
---

# Karakter, Sahne ve Öğe Çıkarma Rehberi

## Karakter Çıkarma Kuralları

Çıkarılan karakter alanları (`save_dedup_characters` aracı parametreleriyle bire bir karşılıklı):
- **name** (zorunlu): karakterin tam adı
- **role**: karakterin konumu — başrol / yardımcı / figüran
- **appearance**: görünüm betimi (300-500 karakter) — cinsiyet, yaş izlenimi, yüz hatları, vücut yapısı, duruş/karizma. **Karakterin kişilik özellikleri ayrıca çıktı olarak verilmez; dışa dönük duruş ve yüz ifadesine dönüştürülerek görünüm betimine işlenir** (ör. "soğuk kişilik" yerine "sert bakışlar, ölçülü ifade, ender gülüş" yazılır)
- **styling**: makyaj-kostüm — saç, kıyafet, makyaj, aksesuar vb.
- **description**: geçmiş hikâye ve karakter ilişkileri (isteğe bağlı ek)

## Sahne Çıkarma Kuralları

Çıkarılan sahne alanları (`save_dedup_scenes` aracı parametreleriyle bire bir karşılıklı):
- **location** (zorunlu): somut mekân adı
- **time**: zaman dilimi (ör. gündüz / akşamüstü / gece yarısı); aynı mekânın farklı zaman dilimi yeni sahne sayılır
- **prompt**: sahne betimi — mekân, dekor düzeni, dönem dokusu, anahtar görsel öğeler (salt arka plan, insan içermez)
- **lighting**: sahnenin ışık-gölge düzeni — ışık kaynakları, renk tonu, aydınlık-karanlık karşıtlığı, atmosfer

## Öğe (Prop) Çıkarma Kuralları

**Temel ilke: az çıkarmak, çok çıkarmaktan iyidir.** Öğeler, beyaz fonlu tekil ürün görseli üretmek ve video yakın çekimlerinde referans vermek için kullanılan yüksek maliyetli varlıklardır; yalnızca kilit öneme sahip öğeler çıkarılmaya değer. Bir bölümde genellikle **0-3 adet** kilit öğe bulunur; 3'ü aşarsa hikâyedeki öneme göre sıralanır ve yalnızca ilk 3'ü tutulur.

Aşağıdaki iki koşulun **her ikisi birden** sağlanmalıdır; biri bile eksikse olmaz:
1. **Doğrudan hikâyeyi ilerletir**: öğenin ortaya çıkması, el değiştirmesi, zarar görmesi ya da bulunması olay örgüsünde dönüş tetikler (ör. cinayet silahı, yadigâr, kritik belge, nişan hediyesi, kilit kanıt).
2. **Ayrı bir görsel üretmeye değer**: sonraki storyboard'larda yakın çekim verilecek ya da tekrar tekrar görünecek; sabit bir görünümü olmalı.

**Üç kontrol sorusu** (her aday öğe için kendine sor ve yanıtla; biri bile "hayır"sa öğeyi bırak):
- ① Çıkarıldığında hikâye hâlâ ayakta kalıyor mu? → Ayakta kalıyorsa **çıkarma** (yalnızca dekor niteliğinde bir fon öğesidir)
- ② Yalnızca karakterin gündelik kullandığı bir eşya mı (telefon, çubuk, bardak, sigara, şemsiye)? → Öyleyse **çıkarma**
- ③ Sahne dekorunun bir parçası mı (masa-sandalye, lambalar, kapı-pencere, duvar süsü, sofra takımı)? → Öyleyse **çıkarma** (bunlar sahne betimine aittir)

**Öğe sayılmayan tipik örnekler**: kullanıldığı hâlde hikâyenin gidişatını etkilemeyen sıradan eşyalar; sahne dekoru ve mobilya; yalnızca bir kez anılıp bir daha hiç geçmeyen eşyalar; karakterin olağan giysileri (karakter kostümüne yazılır).

Koşullara uyan hiçbir öğe yoksa **zorla öğe üretme**; `save_dedup_props` çağrısında boş dizi geçmek yeterlidir.

Çıkarılan öğe alanları (`save_dedup_props` aracı parametreleriyle bire bir karşılıklı):
- **name** (zorunlu): öğe adı
- **type**: tür — gündelik / silah / ulaşım / dekorasyon / belge vb.
- **description**: eşyanın dış görünüşü — yalnızca eşyanın kendi fiziksel görünümü betimlenir (malzeme, renk, şekil, boyut, eskilik derecesi, yıpranma izleri vb.); hikâyeedeki kullanım amacı yazılmaz, karakterlerle ya da başka varlıklarla ilişkisine girilmez

Öğelerin **görsel promptu çıktılanmasına gerek yoktur** — öğenin nihai promptu, görsel üretiminden önce Prompt Üretim Agent'ı tarafından ayrıca oluşturulur (beyaz fonlu tekil ürün standardı).

## Kullanım Adımları

1. Geçerli bölümün senaryosunu okumak için `read_script_for_extraction` çağır
2. Projedeki mevcut karakterleri ve geçerli bölüme bağlı karakterleri görmek için `read_existing_characters` çağır
3. Projedeki mevcut sahneleri ve geçerli bölüme bağlı sahneleri görmek için `read_existing_scenes` çağır
4. Projedeki mevcut öğeleri ve geçerli bölüme bağlı öğeleri görmek için `read_existing_props` çağır
5. Yalnızca geçerli bölümde gerçekten yer alan karakter, sahne ve öğeleri çıkar
6. Karakterleri kaydetmek ve otomatik olarak geçerli bölüme bağlamak için `save_dedup_characters` çağır
7. Sahneleri kaydetmek ve otomatik olarak geçerli bölüme bağlamak için `save_dedup_scenes` çağır
8. Öğeleri kaydetmek ve otomatik olarak geçerli bölüme bağlamak için `save_dedup_props` çağır

## Geçerli Bölüm Kuralları

- Amaç, "geçerli bölümün" gereksinim duyduğu karakter, sahne ve öğeleri tamamlamaktır; tüm projeyi yeniden taramak değildir
- Projede zaten var olup geçerli bölüme bağlı olmayan bir varlık yine de yeniden kullanılır ve geçerli bölüme bağlanır
- Tekilleştirme kuralları: karakter/öğeler isimle birebir eşleştirilir, sahneler 【mekân+zaman dilimi】 ile birebir eşleştirilir; eşleşen varlık öncelikle yeniden kullanılır, tekrar oluşturulmaz
- Yakın isim tekilleştirme: ad, parantez içinde bir niteleme ya da takma ad taşıyorsa parantezden önceki ana kısım karşılaştırılır (ör. "Zeynep (ana karakter)" ile "Zeynep" aynı karakter/öğe sayılır, mevcut olan yeniden kullanılır); read_existing_characters / read_existing_props tarafından döndürülen normalized_name normalleştirilmiş addır, sahnede normalized_location aynı şekilde iş görür; yargıyı buna göre ver
