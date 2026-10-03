---
name: video-prompt
description: Chuẩn prompt video — sinh prompt sinh video chia phân đoạn theo thời gian, cho phép cắt cảnh bên trong đoạn, dựa trên nội dung đoạn phân cảnh
---

# Prompt video (đoạn phân cảnh → video_prompt)

Dựa trên description của một đoạn phân cảnh (chứa cấu trúc tiểu cảnh 【镜头N】 cùng thoại/lời dẫn) / atmosphere / duration, sinh ra `video_prompt` dùng để điều khiển việc sinh video AI. **Một đoạn phân cảnh = một đoạn video 8-15 giây, cho phép cắt cảnh bên trong**: giữa các đoạn với nhau có thể là những ống kính khác nhau (đổi cỡ cảnh/góc máy/đối tượng), nối với nhau bằng cắt cứng; nhưng **từ đầu đến cuối không vượt sang bối cảnh khác**, không hồi tưởng.

## Định dạng

**Dòng đầu tiên của `video_prompt` là dòng đầu đề thông tin**: trước tiên giới thiệu video này có những nhân vật và bối cảnh nào, sau đó mới nối đến các phân đoạn thời gian. Nhân vật, bối cảnh nhất loạt dùng @ để tham chiếu (lúc sinh sẽ được thay bằng nhãn ảnh tham chiếu tương ứng, để mô hình video trước tiên khớp được "ai" và "ở đâu").

```
Nhân vật xuất hiện: @Minh, @Hồng; Bối cảnh: @Quán cà phê.
0-3 giây: @Quán cà phê, cận cảnh, ống kính hơi nhấp nhô như hơi thở và từ từ đẩy gần về phía @Minh, anh cúi đầu nhìn điện thoại, ngón tay gõ liên tục lên mặt bàn, biểu cảm lo âu.
3-6 giây: cắt tới toàn cảnh phía cửa, chuông cửa vang lên, @Hồng đẩy cửa bước vào, kéo theo một luồng gió lạnh.
6-9 giây: cắt về trung cảnh, @Hồng mỉm cười bước về phía Minh rồi ngồi xuống, Minh nói:「Cuối cùng em cũng đến rồi.」
```

Quy tắc dòng đầu đề:
- Chỉ liệt kê những nhân vật thực sự xuất hiện trong đoạn phân cảnh này và bối cảnh được gắn kết, không liệt kê những cái không xuất hiện
- Khi có đạo cụ xuất hiện rõ rệt có thể bổ sung vào dòng đầu đề (ví dụ `; Đạo cụ: @Bức thư`)
- Dòng đầu đề đứng riêng một dòng, kết thúc bằng dấu chấm, phía sau là các phân đoạn thời gian

Chia theo 3 giây một phân đoạn, mỗi phân đoạn riêng một dòng, phân tách bằng xuống dòng, các khoảng thời gian nối tiếp liên tục (không chồng lấp, không bỏ trống).

## Ánh xạ với mô tả phân cảnh

`description` là nguồn nội dung duy nhất của video_prompt (hình ảnh, hành động, thoại, lời dẫn đều nằm trong đó), quy tắc chuyển đổi:

- Mỗi `【镜头N】` trong `description` ánh xạ thành **1-2 phân đoạn 3 giây liên tiếp**, thứ tự trùng khớp, không bỏ sót, không gộp chung, không thêm tiểu cảnh mới
- Thoại/lời dẫn được trích từ 「Tên nhân vật nói:「…」」「Lời dẫn:…」 bên trong `【镜头N】` tương ứng, phân bổ vào các phân đoạn được ánh xạ của tiểu cảnh đó; **không sáng tạo thoại mới ngoài description**
- Hành động trên khung hình lấy `description` làm chuẩn; `atmosphere` chỉ dùng để bổ sung mô tả ánh sáng, tông màu và không khí cho từng phân đoạn

## Cấu trúc bên trong phân đoạn

Mỗi phân đoạn tổ chức nội dung theo thứ tự này (có thể lược bỏ mục không có nội dung, nhưng hành động/hình ảnh bắt buộc phải có):

**Khoảng thời gian ＋ @tham chiếu bối cảnh ＋ cỡ cảnh/chuyển máy ＋ @tham chiếu nhân vật＋hành động chủ thể·biểu cảm ＋ thoại/lời dẫn ＋ không khí ánh sáng**

- **Phân đoạn đầu tiên bắt buộc thiết lập không gian**: bối cảnh + vị trí máy quay + vị trí và trạng thái của nhân vật, để khán giả nhìn một cái biết ngay đang ở đâu, xem ai
- **Cắt cảnh**: phân đoạn sau khi cắt mở đầu bằng từ nối như "cắt tới/cắt về", đồng thời giao lại cỡ cảnh và chủ thể; điểm cắt nên thẳng hàng với cấu trúc `【镜头N】` trong `description` của phân cảnh
- **Cỡ cảnh/chuyển máy (quy tắc bắt buộc)**: mỗi phân đoạn bắt buộc đồng thời ghi rõ **cỡ cảnh** (cận cảnh/trung cảnh/toàn cảnh/đặc tả) và **chỉ lệnh di chuyển ống kính**; bên trong một tiểu cảnh chuyển máy liên tục, sau khi cắt cảnh có thể đổi cách chuyển máy. Cách viết chuyển máy ＝ 「cỡ cảnh khởi đầu ＋ cách vận động ＋ tốc độ/nhịp điệu」, ví dụ "trung cảnh đẩy chậm đều đến đặc tả gương mặt", "lia ngang đồng bộ với nhân vật, nền chảy parallax". Cấm cả đoạn chỉ viết "ống kính cố định" mà không có thông tin vận động — ống kính phải "động" lên (dời vị trí, zoom, bám theo, nhấp nhô như hơi thở đều được), tránh khung hình tĩnh kiểu PPT. Từ vựng chuyển máy xem phần 「chuẩn chuyển máy」 bên dưới
- **Hành động**: mỗi phân đoạn một hành động chính, động từ cụ thể nhìn thấy được (đi, quay người, ngẩng đầu, nắm chặt, khựng lại)
- **Cảm xúc toàn bộ chuyển thành mô tả nhìn thấy được**: đừng dùng từ trừu tượng kiểu "anh ấy rất buồn/không khí căng thẳng", hãy viết thành "anh ấy cúi đầu, ngón tay nắm chặt miệng cốc, hơi thở trở nên nặng nề"
- **Thoại/lời dẫn**: thoại viết 「Tên nhân vật nói:「lời thoại」」, lời dẫn viết 「Lời dẫn: nội dung」; thoại dài 3 giây không đọc hết thì tách ra nhiều phân đoạn; phân đoạn không thoại có thể viết âm thanh môi trường/âm thanh hành động (ví dụ "máy móc gầm rú liên tục")

## Quy tắc tham chiếu

- `@Tên bối cảnh` — tham chiếu bối cảnh, tên phải hoàn toàn trùng khớp với địa điểm trong danh sách bối cảnh
- `@Tên nhân vật` — tham chiếu nhân vật, tên phải hoàn toàn trùng khớp với tên trong danh sách nhân vật
- `@Tên đạo cụ` — tham chiếu đạo cụ, tên phải hoàn toàn trùng khớp với tên trong danh sách đạo cụ; tham chiếu đạo cụ khi nó hiển thị rõ ràng trong khung, được sử dụng hoặc được đặc tả
- Khi sinh, `@tên` sẽ tự động được thay bằng nhãn ảnh tham chiếu tương ứng (ví dụ `@Minh` → `@Ảnh1Minh`), do đó tên phải khớp chính xác tuyệt đối, không viết tắt hay thêm ký hiệu thừa
- **Mỗi phân đoạn ít nhất một tham chiếu @ để neo khung hình**; phân đoạn nào có nhân vật xuất hiện bắt buộc @ nhân vật đó; chỉ tham chiếu bối cảnh/nhân vật/đạo cụ mà đoạn phân cảnh này đã gắn kết

## Quy tắc trục thời gian

- Số phân đoạn = duration của đoạn phân cảnh ÷ 3 giây (làm tròn lên), tổng các khoảng thời gian của từng phân đoạn bắt buộc bằng tổng thời lượng của cả đoạn
- Nhịp nội dung: phân đoạn đầu thiết lập → các đoạn giữa đẩy tiến hành động/xung đột → đoạn cuối hạ xuống kết quả hoặc điểm cảm xúc

## Chuẩn chuyển máy

Mỗi khoảng thời gian đều phải có chuyển động ống kính, chọn từ kho từ vựng dưới đây và giữ nhất quán với ý đồ chuyển máy trong trường `description`/`movement` của phân cảnh (description viết kiểu chuyển máy nào thì video_prompt triển khai đúng kiểu đó; khi description không viết, tự chọn kiểu khớp nhất theo nội dung khung hình):

- **Tự sự cơ bản**: đẩy chậm (trung cảnh→đặc tả, tốc độ đều, nền dần nhòe), kéo xa hé lộ (đặc tả→toàn cảnh, nhanh trước chậm sau), lia ngang bám theo (di chuyển đồng bộ với nhân vật, nền chảy parallax), nâng hạ nhìn từ trên cao (dâng lên/hạ xuống thẳng đứng thể hiện không gian), ôm cung vòng quanh (lấy nhân vật làm tâm vòng 90-180 độ), bước đi góc nhìn thứ nhất (ở tầm mắt, nhấp nhô nhẹ như hơi thở)
- **Cảm xúc – không khí**: cầm tay thở dốc (rung nhẹ, dữ dội hơn sau chuyển động), góc nhìn rình mò (khe cửa/khe cửa sổ che chắn tiền cảnh), xung mạch đập (đẩy–kéo đồng bộ nhịp cảm xúc, bình thản đẩy chậm/căng thẳng đẩy nhanh), bám hơi thở (hít vào đẩy nhẹ, thở ra kéo chậm)
- **Chi tiết tâm lý**: hội tụ ánh nhìn (từ từ đẩy gần vật bị nhìn chằm chằm, dịch chuyển tiêu điểm), rùng mình khiếp sợ (rung vi mô không đều), ôm quanh dịu dàng (vòng chậm góc nhỏ, tiêu điểm khóa gương mặt), đuổi theo tốc độ cao (bám sát mục tiêu di chuyển, nhòe động), dệt xuyên trận đấu (chuyển cắt nhanh giữa hai bên giao đấu), bổ nhào từ trên cao (lao xuống từ độ cao, chạm đất rung nhẹ)
- **Giao đấu tốc độ cao**: chỉ khi `description` của phân cảnh viết rõ chuyển máy giao đấu thì triển khai nguyên văn theo description (vị trí máy, tốc độ, thông số không được mất một thứ nào): đẩy kính thấp tốc độ cao, bám sát mặt đất, hất máy lên nhanh, theo sát cận kề cực hạn, đẩy ngược đổi tiêu điểm, kéo xa nhanh kèm vệt đuôi, khoảnh khắc trúng đòn 0.15 giây làm nhòe tốc độ cao, chấn động shake 0.3 giây
- **Góc nhìn đặc biệt**: ngước chụp cực thấp, nghiêng góc Hà Lan, cận cảnh qua vai, góc nhìn chủ quan
- **Chuyển cảnh nhịp điệu**: vẩy máy nhanh (hướng vẩy trùng với hướng vận động của phân đoạn kế tiếp), chuyển cảnh che chắn (vật tiền cảnh quét qua che khít khoảnh khắc cắt), phanh gấp đóng khung (giảm tốc đến đóng khung tĩnh — chỉ dành cho phân đoạn điểm nổ)

Yêu cầu cách viết:
- Chỉ lệnh chuyển máy phải gắn liền với cỡ cảnh và tốc độ: "từ toàn cảnh từ từ đẩy gần đến trung cảnh", đừng chỉ viết "đẩy máy"
- Trạng ngữ tốc độ cụ thể: tốc độ đều/chậm rãi/cấp tốc/nhanh trước chậm sau/từ chậm đến nhanh
- Một phân đoạn một kiểu chuyển máy; trong đoạn chuyển máy liên tục, chỉ đổi tại điểm cắt cảnh
- Bullet time/đặc tả slow-motion/ống mắt cá/tiểu cảnh mô hình là kỹ xảo điểm xuyết, chỉ dùng khi `description` của phân cảnh viết rõ, một tập tối đa 1-2 chỗ
- Rung tay cầm, nhấp nhô hơi thở thuộc "vi vận động", dùng được cho những phân đoạn vốn định viết ống kính cố định, thay thế cho sự tĩnh lặng hoàn toàn

## Những điều nghiêm cấm

- Chuyển cắt vượt bối cảnh, hồi tưởng (một phân đoạn chỉ diễn ra trong một bối cảnh)
- Tham chiếu bối cảnh/tên nhân vật ngoài danh sách
- Mô tả tâm lý trừu tượng, ẩn dụ văn chương (mô hình chỉ nhận hình ảnh nhìn thấy được)
- Diễn xuất quá mức: không viết thét lên, gào rú, om sòm, khóc nấc; hoảng sợ viết thành vi phản ứng (đứng hình, đồng tử co lại, hít ngược khí, lùi nửa bước), thoại dùng giọng điệu và âm lượng thường ngày (khi tình tiết cực đoan thực sự cần bùng nổ, viết rõ 「cảm xúc bùng nổ」 tại phân đoạn đó để ghi đè)
- Slow-motion và kéo dài bằng tĩnh lặng: mặc định không dùng slow-motion, không viết ánh nhìn tĩnh kéo dài; ngoại lệ: tiểu cảnh điểm nổ mà `description` của phân cảnh viết rõ có bullet time/đặc tả slow-motion/phanh gấp đóng khung, thì dùng theo description. Mỗi phân đoạn vẫn cần chuyển động ống kính hoặc đẩy tiến hành động nhìn thấy được, không cho phép "ống kính tĩnh thuần túy"
- Ngôn ngữ không khớp với chỉ lệnh ngôn ngữ của phiên hội thoại

## Lưu trữ

Gọi `update_storyboard` chỉ cập nhật trường `video_prompt` của đoạn phân cảnh này, không sửa các trường khác, không tái phân rã cả tập. Nền tảng sẽ tự động bổ sung bộ vệ binh diễn xuất và nhịp điệu khi thực hiện yêu cầu sinh thực tế, trong prompt không cần viết lại các yêu cầu này.
