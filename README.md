#### Incomplete issues
    Thuật toán chọn peer để request
    Xóa (hoặc deactivate) peer nếu peer offline trong tracker
    Tình trạng request lặp lại tới những peer không có requested piece (quản lý bitfield cho mỗi peer)
#### How to run
1. Chạy py tracker.py
Sau khi chạy tracker sẽ hiển thị ra ip
Lấy ip này đổi tracker_url trong file torrent.py = 'ip_vừa_lấy_được:22236'
Chạy py torrent.py đêt tạo file torrent mới

2. Chạy peer: py peer.py --peer-port PORT_NUMBER --peer-name PEER_NAME
    + upload: upload ./torrent/test.torrent (đảm bảo ở trong thư mục peer-complete-file{PEER_NAME} có file đầy đủ)
    + download: download ./torrent/test.torrent
