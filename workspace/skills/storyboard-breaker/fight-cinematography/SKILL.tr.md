---
name: fight-cinematography
description: Yüksek hızlı dövüş kamera hareketi el kitabı — dövüş/kovalamaca/patlama parçaları için kamera konumu formülleri, hız notasyonları ve prompt yazımı
---

# Yüksek Hızlı Dövüş Kamera Hareketi El Kitabı (dövüş/yüksek hızlı eylem parçalarına özel)

## Ne Zaman Devreye Girer (otomatik yargı)

Parçada ya da parça içindeki alt planda **dövüş, hücum, kovalamaca, kaçıp karşılık verme, uçarak tekme, ağır vuruş patlaması, darbeyle savrulma** gibi yüksek hızlı eylemler göründüğünde, kamera hareketi bu el kitabındaki "kamera konumu formülleri" ile "hız notasyonları" arasından seçilir; temel kamera hareketi söz dağını önceleyerek kullanılır; diyalog parçaları, zemin hazırlama parçaları ve geçiş parçalarında bu el kitabı kullanılmaz.

Temel mantık yalnızca iki noktadır: **hız** ve **öngörü** — hız üret, hız büyüt. Kamera hareketi üç amaca hizmet eder:
1. Seyircinin eylemin izini net görmesini sağlamak
2. Saldırı yönünün darbe gücünü pekiştirmek
3. Kamera hızıyla baskı hissi kurmak

## Kamera Konumu Formülleri (10 madde)

Her madde ＝ kamera konumu/hareket bileşimi ＋ uygun vuruş türü ＋ prompt yazımı (yazım, `description` alanının 【镜头N】 başlığına doğrudan gömülebilir):

| # | Formül | Uygun vuruş türü | Prompt yazımı |
|---|---|---|---|
| 1 | Başlangıç çarpışması: alçak kamera konumu＋ani hızlı yaklaşma | Ağır yumruk, çarpışma, ilk temas | Kamera 0.5 metre alçak açıda; kamera aşağıdan yukarıya ani hızlı push-in yapar, iki tarafın yüksek hızlı çarpışmasının savurduğu tozu ve şok dalgasının hacim hissini yakalar, LOW açı baskı hissini güçlendirir |
| 2 | Yandan takip: dolanma çekimi＋odak değişimi | Üst üste vuruşlar, saldırı-savunma geçişi, dinamik karşılıklı saldırı | ORBIT dolanması saldırganın arkasından yarım kuşatır, odak darbe yiyenin saç tellerine ve kıyafet ucuyla kilitlenir, isabet anında odak değişir |
| 3 | Yere yapışık takip: yere yapışık açı＋alçak konumlu takip | Süpürme tekmesi, yere düşüp yuvarlanma, alçak seviye eylemler | Kamera yere yapışık alçak açıyla bacak hareketlerini takip ederek süpürür, yerdeki kırıntılar yüzünün önünden geçer |
| 4 | Havada izleme: alçak konumdan aşağıdan çekim＋ani hızlı yukarı savırma | Uçarak tekme, döner tekme, havada üst üste tekmeler | Alçak konumdan aşağıdan çekim; TILT UP ani hızlı yukarı savırma kişinin havaya yükselişini izler, havada asılı kalma hissi vurgulanır |
| 5 | İsabet anı: ani duruş dondurma＋hafif titreme | Isabetli vuruş, patlama noktası | İsabet anında yakın çekim; görüntü 0.15 saniye yüksek hızla bulanıklaşır, darbe yiyen bölgede hayalet görüntü kalır, kamera hafif geri tepme sarsıntısı yapar |
| 6 | Darbeyle savrulma: ani hızlı uzaklaşma＋iz sürme | Ağır darbeyle uçma, geri savrulma | Kamera ani hızla uzaklaşır, kişinin darbeyle savrulma izi boyunca takip eder, arka plan derinliğe doğru yırtılır |
| 7 | Azami yakınlık: takip açısı＋DOLLY ilerleme | Zincirleme yumruklar, kombinasyon vuruşları | DOLLY yatay ilerleme; kamera boğuşan iki tarafa azami yakınlığa sokulur, seyirci yumruk rüzgârının baskısını hisseder |
| 8 | Kaçış ve karşılık: ters yönlü yaklaşma＋odak değişimi | Kaçınma, savunmadan karşılık | Kamera saldırganın arkasından ani hızla ileri itilir, PAN yatay savurmayla karşılık yönüne döner, PUSH ani hızla karşılık hareketine yaklaşır, odak saldırgandan karşılık verene bir anda geçer |
| 9 | Alçak açıdan karşılık: aşağıdan açı＋ani hızlı uzaklaşma | Alttan gelen karşılık, havada vuruş | Alçak açıdan aşağıdan çekimle açılır, kişi havaya yükselirken kamera ani hızla uzaklaşır, aşağıdan yakın çekimden bir anda havada genel plana açılır |
| 10 | Vuruş kapanışı ve dondurma: yavaş yaklaşma yakın plan＋yavaş geri çekilme | Vuruş serisini kapatma, poz verme, bir sonraki vuruşa güç toplama | MCU orta-yakın plan yavaş yaklaşmayla kişinin pozu dondurulur; ardından PULL yavaş geri çekilmeyle arka plan flu hâle gelir, bir sonraki vuruşun patlamasından hemen önceki gerilim korunur |

## Hız Notasyonları (4 tür, kamera konumu formüllerinin üzerine eklenir)

| Notasyon | Kullanım yeri | Etki | Yazım |
|---|---|---|---|
| Swift hızlı takip | Hücum, atılım, kovalamaca, göğüs göğüse hareket | Gerilim, hız hissi, güçlü ritim | Orta plandan ani hızlı yaklaşma-uzaklaşma; ön plan öğeleri hızla önünden geçer, arka planda yatay hareket bulanıklığı oluşur |
| Whip savurma | Dönüş, kaçınma, isabet anı, yön değişimi | Anilik, patlama hissi | WHIP hedefle temas anında süpürür, odak bir anda darbe yiyene kesilir |
| Gentle yavaş geri çekilme | Baskının bitişi, tozun dağılması, savaş alanı düzeninin gösterimi | Kapanış sonrası gerilim | Kamera çatışmanın en yoğun olduğu noktadan yavaşça geri çekilir, odak karakterde kilitli kalır, arka plandaki savaş alanı giderek açılır |
| Shock sarsıntı | Ağır vuruş, patlama, kırılma, çöküş | Derin sarsıntı | İsabet anında kamera 0.3 saniye shake yapar, görüntü hafifçe titrer, yerdeki kırıntılar şok dalgası yönünde savrulur |

## Yazım Kuralları (storyboard alanlarıyla eşleşme)

- `movement`: yukarıdaki tablodan formül adı ya da bileşim seçilir (ör. "havada izleme (alçak konumdan aşağıdan çekim＋ani hızlı yukarı savırma)"); bir alt plana bir ana kamera hareketi
- `description` alanının 【镜头N】 bölümü: alt planın başına eksiksiz çekim yönergesi yazılır ＝ **kamera konumu/açı ＋ hareket biçimi ＋ hız zarfı ＋ plan ölçeği**; sayısal değerler (0.5 metre, 0.15 saniye, 0.3 saniye) aynen korunur — video-prompt, description'ı bölüm bölüm açar; sayı kaybedilirse hız hissi de kaybedilir
- Hız zarfları somut olmalıdır: ani hızlı / sabit hız / yavaş / önce hızlı sonra yavaş; yalnızca "yaklaşma", "takip" yazmak yasaktır
- Bir bölümde bir kamera hareketi, bölüm içinde kesintisiz; dövüş parçalarında alt planlar arasında formlara sert geçiş serbesttir, kesme noktaları 【镜头N】 ile hizalanır
- **Hız-yavaşlık dengesi**: 2-3 ardışık ani hızlı alt plandan sonra, bir Gentle yavaş geri çekilme ya da isabet dondurmasıyla nefeslenilir ve bir sonraki patlamaya girilir; bölümün tamamı sürekli hızlı olursa her şey birbirine karışır, tamamı yavaş olursa baskı hissi kaybolur
- Bullet time/ağır çekim yine vurgu numarasıdır; temel standardın bölüm başına 1-2 kez üst sınırına uyar ve yalnızca isabet anında ya da vuruş kapanışı dondurmada kullanılır

## Her Yerde İşleyen Şablon (doğrudan uygula)

- **Yüksek hızlı açılış**: formül 1 (alçak konumdan ani push-in) ＋ Swift
- **Üst üste vuruş parçası**: formül 7 (azami yakınlık DOLLY) ↔ formül 2 (ORBIT odak değişimi), alt planlar arasında sert kesme
- **Kaçış ve karşılık**: formül 8 (ters yönlü yaklaşma ve odak değişimi) ＋ Whip
- **Ağır vuruş patlaması**: formül 5 (isabet anı 0.15 saniye bulanıklaştırma) ＋ Shock (0.3 saniye shake) → formül 6 (ani hızlı uzaklaşma ve iz sürme)
- **Vuruş kapanışı dondurma**: formül 10 (MCU yavaş yaklaşma → Gentle yavaş geri çekilme), bir sonraki vuruşa güç biriktirir

## Tek Cümlelik Özet

Dövüş kamera hareketinin özü "**sürekli hareket hâlde olmak**"tır — kamera hareketiyle hız hissi ve baskı seyirciye aktarılır; ani hız ile kısa süreli dondurma dönüşümlü kullanılır ve vuruş ile vuruş arasındaki boşluklarda güç biriktirme ile geçiş tamamlanır.
