---
name: extractor
description: Chuẩn và phương pháp trích xuất nhân vật, bối cảnh và đạo cụ
---

# Hướng dẫn trích xuất nhân vật, bối cảnh và đạo cụ

## Chuẩn trích xuất nhân vật

Các trường nhân vật trích xuất (tương ứng một-một với tham số công cụ `save_dedup_characters`):
- **name** (bắt buộc): tên đầy đủ của nhân vật
- **role**: định vị nhân vật — vai chính/vai phụ/vai quần chúng
- **appearance**: mô tả ngoại hình (300-500 chữ) — giới tính, cảm giác độ tuổi, ngũ quan, vóc dáng, khí chất. **Đặc điểm tính cách của nhân vật không xuất hiện riêng rẽ, mà phải chuyển hóa thành khí chất và thần thái bề ngoài, đan xen vào mô tả ngoại hình** (ví dụ "tính cách lạnh lùng" nên viết thành "ánh mắt lạnh lùng, biểu cảm tiết chế, hiếm khi có ý cười")
- **styling**: tạo hình – trang điểm — kiểu tóc, trang phục, trang điểm, phụ kiện v.v.
- **description**: tiểu sử và quan hệ nhân vật (bổ sung tùy chọn)

## Chuẩn trích xuất bối cảnh

Các trường bối cảnh trích xuất (tương ứng một-một với tham số công cụ `save_dedup_scenes`):
- **location** (bắt buộc): tên địa điểm cụ thể
- **time**: khung thời gian (ví dụ ban ngày/hoàng hôn/nửa đêm khuya); cùng địa điểm nhưng khác khung thời gian được tính là bối cảnh mới
- **prompt**: mô tả bối cảnh — không gian, cách bài trí, chất liệu thời đại, các yếu tố hình ảnh then chốt (thuần nền, không chứa nhân vật)
- **lighting**: ánh sáng – bóng đổ của bối cảnh — nguồn sáng, tông màu, tương phản sáng tối, không khí

## Chuẩn trích xuất đạo cụ

**Nguyên tắc cốt lõi: thà trích ít còn hơn trích nhiều.** Đạo cụ là tài sản chi phí cao, dùng để tạo ảnh đơn phẩm nền trắng và phục vụ cảnh đặc tả tham chiếu trong video; chỉ những đạo cụ then chốt cho cốt truyện mới đáng trích xuất. Thông thường một tập chỉ có **0-3** đạo cụ then chốt; nếu vượt quá 3, xếp theo mức độ quan trọng với cốt truyện và chỉ giữ 3 cái đầu.

Phải **đồng thời thỏa mãn** cả hai điều kiện sau, thiếu một cũng không được:
1. **Trực tiếp đẩy tiến cốt truyện**: sự xuất hiện, bàn giao, hư hỏng hoặc bị phát hiện của vật phẩm này sẽ tạo ra bước ngoặt tình tiết (ví dụ hung khí, vật tín, tài liệu then chốt, quà định tình, chứng cứ then chốt).
2. **Đáng để tạo ảnh riêng**: phân cảnh về sau sẽ cho nó cảnh đặc tả hoặc nó xuất hiện lặp lại nhiều lần, cần ngoại hình cố định.

**Ba câu hỏi tự vấn** (tự hỏi tự trả lời với từng đạo cụ ứng viên, câu nào trả lời "không" thì từ bỏ):
- (1) Bỏ nó đi thì cốt truyện có vẫn đứng vững không? → Nếu vẫn vững thì **không trích xuất** (nó chỉ là phông nền kiểu đạo cụ)
- (2) Nó có chỉ là vật dụng thường ngày nhân vật dùng tùy tay không (điện thoại, đũa, cốc nước, thuốc lá, ô)? → Nếu đúng thì **không trích xuất**
- (3) Nó có phải là một phần trong bài trí của bối cảnh không (bàn ghế, đèn, cửa – cửa sổ, tranh treo tường, bộ đồ ăn)? → Nếu đúng thì **không trích xuất** (những thứ này thuộc về mô tả bối cảnh)

**Các kiểu điển hình không tính là đạo cụ**: vật dụng bình thường dùng tùy tay nhưng không ảnh hưởng hướng đi của cốt truyện; bài trí và đồ nội thất của bối cảnh; vật phẩm chỉ được nhắc đến một lần rồi không có hạ văn; trang phục thường ngày của nhân vật (quy về phần tạo hình nhân vật).

Nếu không có đạo cụ nào đạt điều kiện, **đừng ép trích xuất**, khi gọi `save_dedup_props` chỉ cần truyền mảng rỗng là được.

Các trường đạo cụ trích xuất (tương ứng một-một với tham số công cụ `save_dedup_props`):
- **name** (bắt buộc): tên đạo cụ
- **type**: phân loại — hàng ngày/vũ khí/phương tiện giao thông/trang trí/tài liệu v.v.
- **description**: ngoại hình của vật phẩm — chỉ mô tả diện mạo vật lý của chính vật phẩm (chất liệu, màu sắc, hình dáng, kích thước, mức độ mới–cũ, dấu vết mài mòn v.v.), không viết công dụng của nó trong cốt truyện, không đề cập đến sự liên quan với nhân vật hay sự vật khác

Đạo cụ **không cần xuất prompt ảnh** — prompt cuối cùng của đạo cụ do Agent tạo prompt chuyên trách sinh ra trước khi vẽ ảnh (chuẩn đơn phẩm nền trắng).

## Các bước thực hiện

1. Gọi `read_script_for_extraction` để đọc kịch bản của tập hiện tại
2. Gọi `read_existing_characters` để xem các nhân vật đã có trong dự án và nhân vật đã liên kết với tập hiện tại
3. Gọi `read_existing_scenes` để xem các bối cảnh đã có trong dự án và bối cảnh đã liên kết với tập hiện tại
4. Gọi `read_existing_props` để xem các đạo cụ đã có trong dự án và đạo cụ đã liên kết với tập hiện tại
5. Chỉ trích xuất những nhân vật, bối cảnh và đạo cụ mà tập hiện tại thực sự dính đến
6. Gọi `save_dedup_characters` để lưu nhân vật và tự động liên kết vào tập hiện tại
7. Gọi `save_dedup_scenes` để lưu bối cảnh và tự động liên kết vào tập hiện tại
8. Gọi `save_dedup_props` để lưu đạo cụ và tự động liên kết vào tập hiện tại

## Quy tắc về tập hiện tại

- Mục tiêu là bổ sung đầy đủ nhân vật, bối cảnh và đạo cụ mà "tập hiện tại" cần, không phải quét lại toàn bộ dự án
- Nếu đã tồn tại trong dự án nhưng tập hiện tại chưa liên kết, vẫn nên tái sử dụng và liên kết vào tập hiện tại
- Quy tắc khử trùng lặp: nhân vật/đạo cụ khớp chính xác theo tên; bối cảnh khớp chính xác theo 【địa điểm + khung thời gian】; khi trúng khớp thì ưu tiên tái sử dụng, không tạo trùng lặp
- Khử trùng lặp theo tên gần giống: khi tên có định vị trong ngoặc hoặc tên gọi khác, so sánh theo phần chính trước ngoặc (ví dụ 「Lâm Tiểu Vũ (nhân vật chính)」 và 「Lâm Tiểu Vũ」 được xem là cùng một nhân vật/đạo cụ, tái sử dụng cái đã có); normalized_name mà read_existing_characters / read_existing_props trả về chính là tên đã được chuẩn hóa, normalized_location của bối cảnh cũng tương tự, cứ dựa vào đó để phán đoán
