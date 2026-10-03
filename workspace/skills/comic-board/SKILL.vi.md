---
name: comic-board
description: Chuẩn chuyên môn chuyển thể phân cảnh truyện tranh — nhịp chia khung, mô tả hình ảnh, prompt xuất ảnh và phân bổ lời thoại
---

# Hướng dẫn chuyển thể phân cảnh truyện tranh

## Nguyên tắc chung khi chia khung

- Mỗi chương 8-16 khung; chương ngắn lấy cận dưới, chương nhiều xung đột lấy cận trên
- Nhịp chia khung phục vụ cốt truyện: móc câu mở đầu 1-2 khung, đẩy tiến xung đột 4-8 khung, điểm neo ở kết 1-2 khung
- Mỗi khung một đơn vị hình ảnh độc lập: một hành động, một phản ứng hoặc một lần thiết lập bối cảnh; không nhét hai dòng thời gian – không gian vào cùng một khung
- Các khung liền kề bắt buộc phải thay đổi cỡ cảnh: 3 khung liên tiếp cùng cỡ cảnh là điều tối kỵ

## Chuẩn trường dữ liệu của từng khung

- description (mô tả hình ảnh): nhân vật + hành động + biểu cảm + yếu tố nền, một câu nói rõ "ai đang làm gì"; tạo hình nhân vật phải nhất quán với thế giới quan/thời đại của truyện
- dialogue: chỉ đặt lời thoại hoặc lời dẫn bắt buộc xuất hiện trong khung này, tối đa một câu; thoại lấy nguyên văn từ kịch bản, không tự viết mới; khung không thoại là một thủ pháp nhịp điệu chính đáng
- narration (lời dẫn kiểu truyện tranh liên hoàn, 40–120 chữ, bắt buộc điền ở mọi khung): văn xuôi tự sự ngôi thứ ba, đẩy tiến câu chuyện — chuyện gì đã xảy ra, phản ứng/tâm lý nhân vật, móc câu hoặc bước ngoặt; lời thoại lồng vào lời dẫn (「Ai đó quát:……」); đọc liền mạch toàn bộ lời dẫn của cả tập phải là một câu chuyện hoàn chỉnh, nghiêm cấm những mảnh văn chỉ tạo không khí rời rạc
- composition (bố cục ống kính): cỡ cảnh (toàn cảnh xa/toàn cảnh/trung cảnh/cận cảnh/đặc tả) + góc máy (ngang tầm mắt/nhìn xuống/nhìn lên) + ý đồ bố cục (ví dụ "góc nhìn qua vai", "khoảng trống lớn dồn nén cảm xúc")
- image_prompt (prompt xuất ảnh, tiếng Anh): chủ thể + hành động + môi trường + ánh sáng + bố cục, một đoạn liền mạch 30-60 từ; **không viết từ chỉ phong cách** (phong cách hội họa do hệ thống thống nhất chèn); không đưa chữ thoại vào ảnh; các ràng buộc chất lượng (năm ngón tay/năm ngón chân, tay chân đầy đủ, một nhân vật không bóng kép, biểu cảm tiết chế, hình ảnh không có chữ và watermark) do hệ thống thống nhất bổ sung khi xuất ảnh, không cần viết vào — nhưng phần mô tả hành động tránh cử chỉ tay phức tạp, cảm xúc thể hiện qua tư thế cơ thể và ánh mắt, không viết các từ kiểu gào thét/hét lớn (khi thực sự cần bùng nổ thì viết rõ "cảm xúc bùng nổ"), trong một khung không nên có quá nhiều nhân vật chồng lên nhau

## Thủ pháp kể chuyện bằng hình ảnh

- Bước ngoặt cảm xúc then chốt dùng cảnh đặc tả; giao quan hệ không gian dùng toàn cảnh; mỗi chương ít nhất 1 cảnh toàn cảnh xa để thiết lập cảm giác không gian
- Kịch bản nhiều thoại: tách đoạn thoại dài ra nhiều khung, dùng khung biểu cảm phản ứng để cắt đoạn, tránh "bức tường khung đối thoại"
- Khung điểm neo kết thúc = hình ảnh treo ngờ vực ở mức cao nhất (đóng khung ngay khoảnh khắc trước khi biến đổi xảy ra), kèm một câu thoại hoặc lời dẫn dạng móc câu
- Xen kẽ khung tĩnh lặng và khung bùng nổ: các khung hành động liên tiếp không quá 3 khung, chèn giữa chúng khung phản ứng hoặc khung cảnh trống để lấy hơi

## Cân nhắc khi chuyển thể

- Mô tả tâm lý trong kịch bản → chuyển hóa thành gợi ý qua biểu cảm/hành động/bố cục, không vẽ chữ trực tiếp
- Nội dung mang tính chuyển tiếp trong kịch bản → dùng 1 khung cảnh trống hoặc khung chuyển cảnh để lướt qua, tương đương về mặt tự sự
- Giữ lại xung đột và cú lật ngược tình thế mạnh nhất, hy sinh những chi tiết vụn vặt: mỗi khung đều phải "đáng xem"
