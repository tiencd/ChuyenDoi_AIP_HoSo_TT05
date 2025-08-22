# ĐẶC TẢ TỔNG HỢP — GÓI AIP_hoso & METS GỐC  
**Căn cứ:** Phụ lục I, Thông tư 05/2025/TT-BNV  
**Ngày tổng hợp:** 2025-08-22 17:00:00 +0700

---

## 0) Phạm vi & đầu vào
- **Mục tiêu:** Xây dựng chương trình sinh gói **AIP_hoso** (đóng gói OAIS) và **METS.xml gốc** đáp ứng Phụ lục I TT 05/2025/TT-BNV.  
- **Đầu vào:**  
  - Tệp **`metadata.xlsx`** gồm hai sheet đề xuất: `HoSo` (1 dòng/AIP), `TaiLieu` (1 dòng/tài liệu).  
  - **Thư mục chứa PDF** (các tài liệu của hồ sơ).

---

## 1) Chuẩn chung (áp dụng toàn bộ METS)
- **Namespaces:**  
  `xmlns:mets="http://www.loc.gov/METS/"`  
  `xmlns:xlink="http://www.w3.org/1999/xlink"`  
  `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"`  
  `xmlns:csip="https://DILCIS.eu/XML/METS/CSIPExtensionMETS"`
- **Thời gian:** ISO 8601 kèm múi giờ Việt Nam `+07:00`.  
- **Checksum:** `SHA-256`, giá trị hexa 64 ký tự (thống nhất kiểu chữ).  
- **Đường dẫn:** `xlink:href` **tương đối** trong phạm vi gói AIP_hoso.  
- **Quy ước ID:** không trùng lặp trong 1 METS. Gợi ý tiền tố theo loại: `dmd-`, `amd-`, `digiprov-`, `mdref-`, `file-`, `fptr-`, `div-`, `sm-`, `fs-`, `fg-` + `UUID`.  
- **OAIS package type:** `csip:OAISPACKAGETYPE = AIP` (bắt buộc).

---

## 2) Cấu trúc gói AIP_hoso (thành phần & thư mục)

### 2.1 Bảng tổng thành phần
| Đường dẫn | Loại | Bắt buộc | SL | Ghi chú |
|---|---|:--:|:--:|---|
| `AIP_hoso/` | Thư mục | Có | 01 | Tên thư mục gói lấy từ `mets/@OBJID` (thay `:` → `_`). |
| `AIP_hoso/METS.xml` | Tệp | Có | 01 | METS gốc của gói AIP. |
| `AIP_hoso/metadata/descriptive/EAD.xml` | Tệp | Có | 01 | Siêu dữ liệu mô tả tổng thể hồ sơ (EAD). |
| `AIP_hoso/metadata/preservation/PREMIS.xml` | Tệp | Có | 01 | Siêu dữ liệu bảo quản (PREMIS). |
| `AIP_hoso/representations/rep1/` | Thư mục | Có | 01 | Bản đại diện chứa dữ liệu hồ sơ. |
| `AIP_hoso/representations/rep1/METS.xml` | Tệp | Có | 01 | METS của `rep1`. |
| `AIP_hoso/representations/rep1/data/*.pdf` | Tệp | Có | ≥1 | Các tài liệu PDF của hồ sơ. |
| `AIP_hoso/schemas/*.xsd` | Tệp | Có | ≥1 | Lược đồ METS/EAD/PREMIS (tối thiểu METS.xsd + EAD/PREMIS tương ứng). |
| `AIP_hoso/documentation/*` | Thư mục/tệp | Không | — | Tài liệu bổ sung (nếu có). |

### 2.2 Cây thư mục mẫu (rút gọn)
```
AIP_hoso/
  METS.xml
  metadata/
    descriptive/EAD.xml
    preservation/PREMIS.xml
  representations/
    rep1/
      METS.xml
      data/
        File1.pdf
        File2.pdf
  schemas/
    METS.xsd
    EAD.xsd (hoặc EAD_doc.xsd, EAD_media.xsd, ...)
    PREMIS.xsd (nếu muốn xác thực)
  documentation/   (tuỳ chọn)
```

---

## 3) RTM — Yêu cầu chi tiết METS gốc (thuộc tính & ánh xạ)

### 3.1 `<mets>` & `metsHdr/agent`
| Thành phần | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|:--:|---|---|
| `mets/@TYPE` | Có | Cấu hình | `AIP`. |
| `mets/@OBJID` | Có | HoSo.OBJID | `urn:uuid:<uuid>`; tên thư mục gói thay `:` → `_`. |
| `mets/@LABEL` | Khuyến nghị | HoSo.Title | Nhãn gói. |
| `mets/@PROFILE` | Có | Cấu hình | Theo hồ sơ CSIP áp dụng. |
| `csip:OAISPACKAGETYPE` | **Có** | Cấu hình | `AIP`. |
| `metsHdr/@CREATEDATE` | Có | HoSo.CreatedAt | ISO 8601 `+07:00`. |
| `metsHdr/@LASTMODDATE` | Tuỳ | HoSo.LastModAt | Nếu có. |
| `metsHdr/@RECORDSTATUS` | Tuỳ | HoSo.RecordStatus | `NEW|SUPPLEMENT|DELETE` (nếu áp dụng). |
| `agent/@ROLE` | Có | Cấu hình | `CREATOR`, `ARCHIVIST`… |
| `agent/@TYPE` | Có | Cấu hình | `ORGANIZATION`/`INDIVIDUAL`. |
| `agent/name` | Có | Cấu hình | Tên cơ quan/tổ chức tạo AIP. |

### 3.2 `dmdSec` (EAD tham chiếu qua `mdRef`)
**a) `<dmdSec>`**
| Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|:--:|---|---|
| `@ID` | **Có** | Tự sinh | `dmd-<UUID>`. |
| `@CREATED` | Khuyến nghị | Thời điểm sinh EAD | ISO 8601. |
| `@STATUS` | Tuỳ | HoSo.RecordStatus | `CURRENT`/`REVISED`… |

**b) `<dmdSec>/<mdRef …>` → `metadata/descriptive/EAD.xml`**
| Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|:--:|---|---|
| `@ID` | **Có** | Tự sinh | `mdref-<UUID>`. |
| `@LOCTYPE` | **Có** | Cố định | `URL`. |
| `@MDTYPE` | **Có** | Cố định | `EAD` *(hoặc `OTHER` + `OTHERMDTYPE="EAD"`)*. |
| `@MIMETYPE` | **Có** | Cố định | `text/xml`. |
| `@CREATED` | Khuyến nghị | Thời điểm EAD | ISO 8601. |
| `@SIZE` | Khuyến nghị | Từ file EAD | Byte size. |
| `@CHECKSUM` | Khuyến nghị/ Có* | Tính từ file | SHA-256. |
| `@CHECKSUMTYPE` | **Có*** | Cố định | `SHA-256`. |
| `xlink:type` | **Có** | Cố định | `simple`. |
| `xlink:href` | **Có** | Đường dẫn | `metadata/descriptive/EAD.xml`. |

**c) Ánh xạ EAD.xml (từ `HoSo`):** `titleproper` ← `Title`; `unitid` ← `MaHoSo`; `unitdate` (normal từ `PhamViThoiGian_BD/_KT`); `physdesc/extent` ← `SoTo`; `langmaterial` ← `NgonNgu`; `scopecontent` ← `TomTat`; `origination` ← `DonViHinhThanh`; `repository/fonds` ← `PhongLuuTru`…

### 3.3 `amdSec` (PREMIS qua `digiprovMD/mdRef`)
**a) `<amdSec>`**
| Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|:--:|---|---|
| `@ID` | **Có** | Tự sinh | `amd-<UUID>`. |

**b) `<amdSec><digiprovMD …>`**
| Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|:--:|---|---|
| `@ID` | **Có** | Tự sinh | `digiprov-<UUID>`. |

**c) `<amdSec><digiprovMD><mdRef …>` → `metadata/preservation/PREMIS.xml`**
| Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|:--:|---|---|
| `@ID` | **Có** | Tự sinh | `mdref-<UUID>`. |
| `@LOCTYPE` | **Có** | Cố định | `URL`. |
| `@MDTYPE` | **Có** | Cố định | `PREMIS` *(hoặc `OTHER` + `OTHERMDTYPE="PREMIS"`)*. |
| `@MIMETYPE` | **Có** | Cố định | `text/xml`. |
| `@CREATED` | Khuyến nghị | Thời điểm PREMIS | ISO 8601. |
| `@SIZE` | Khuyến nghị | Từ file PREMIS | Byte size. |
| `@CHECKSUM` | Khuyến nghị/ Có* | Tính từ file | SHA-256. |
| `@CHECKSUMTYPE` | **Có*** | Cố định | `SHA-256`. |
| `xlink:type` | **Có** | Cố định | `simple`. |
| `xlink:href` | **Có** | Đường dẫn | `metadata/preservation/PREMIS.xml`. |

**d) Ánh xạ PREMIS.xml:**  
- `object` (file/pdf): format (`application/pdf`), size, fixity SHA-256, creatingApplication (nếu biết).  
- `event`: `ingestion`, `fixity check`, `validation` với `eventDateTime` và `outcome`.  
- `agent`: hệ thống/cơ quan tạo gói.  
- `linking*`: liên kết giữa object–event–agent.

### 3.4 `fileSec` (khai báo tệp & định vị)
**a) `<fileSec>`**
| Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|:--:|---|---|
| `@ID` | **Có** | Tự sinh | `fs-<UUID>`. |

**b) `<fileGrp>`**  
- Dùng `@USE` để phân nhóm: `Schemas`, `Documentation` (tuỳ chọn), `Representations/rep1` (bắt buộc).

**c) `<file …>` trong `fileGrp`**
| Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|:--:|---|---|
| `@ID` | **Có** | Tự sinh | `file-<UUID>`. |
| `@MIMETYPE` | **Có** | TaiLieu.MimeType | `application/pdf` cho PDF. |
| `@SIZE` | Khuyến nghị | Quét file | Byte size. |
| `@CREATED` | Khuyến nghị | Quét file | ISO 8601. |
| `@CHECKSUM` | Khuyến nghị/ Có* | Quét file | SHA-256. |
| `@CHECKSUMTYPE` | Khuyến nghị/ Có* | Cố định | `SHA-256`. |

**d) `<file>/<FLocat …>`**
| Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|:--:|---|---|
| `LOCTYPE` | **Có** | Cố định | `URL`. |
| `xlink:type` | **Có** | Cố định | `simple`. |
| `xlink:href` | **Có** | Đường dẫn | Tương đối trong gói, ví dụ: `representations/rep1/data/File1.pdf`. |

### 3.5 `structMap` (cấu trúc CSIP)
**a) `<structMap …>` gốc**
| Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|:--:|---|---|
| `@ID` | **Có** | Tự sinh | `sm-<UUID>`. |
| `@LABEL` | **Có** | Cố định | `CSIP`. |
| `@TYPE` | Khuyến nghị | Cố định | `logical`. |

**b) `div` cấp 1**
| Vị trí | Bắt buộc | Thuộc tính/Thành phần | Quy tắc/giá trị |
|---|:--:|---|---|
| `div[@LABEL="Metadata"]` | Có | `@ID`, `@LABEL`, `@DMDID`, `@ADMID` | `DMDID` → `dmdSec/@ID`; `ADMID` → `amdSec/@ID`. |
| `div[@LABEL="Schemas"]` | Có | `@ID`, `<fptr @FILEID>` | `FILEID` trỏ tới `<file/@ID>` nhóm Schemas. |
| `div[@LABEL="Representations/rep1"]` | Có | `@ID`, `<mptr>` | `mptr@xlink:href="representations/rep1/METS.xml"`, `xlink:title="METS of rep1"`. |

**c) Có thể bổ sung `div` con cho thứ tự tài liệu** dựa `TaiLieu.ThuTu` và dùng `<fptr FILEID="file-…">` trỏ PDF tương ứng.

---

## 4) Ánh xạ `metadata.xlsx` (đề xuất)

### 4.1 Sheet `HoSo` (1 dòng/AIP — cột tối thiểu)
`OBJID`, `Title`, `RecordStatus`, `CreatedAt`, `LastModAt?`, `DonViHinhThanh`, `PhongLuuTru`, `MaHoSo`, `PhamViThoiGian_BD`, `PhamViThoiGian_KT`, `SoTo`, `DoMat?`, `ThoiHanBaoQuan?`, `NgonNgu`, `TomTat` …

### 4.2 Sheet `TaiLieu` (1 dòng/tài liệu)
`FileName`, `Title`, `NgayTaiLieu`, `ThuTu`, `MimeType(default=application/pdf)`, `FileSize?`, `ChecksumSHA256?`, `CreatedAt?`, `PDF_Version/PDF_A?`, `Trang?`, `NgonNgu?`, `QuyenTruyCap?`, `GhiChuKySo?`, `NguonSoHoa/ThietBi/DoPhanGiai?` …  
> Dấu `?` là trường có thể suy ra tự động khi quét thư mục PDF.

---

## 5) Checklist xác nhận hợp lệ (tối thiểu phải đạt)
- `csip:OAISPACKAGETYPE = AIP` xuất hiện ở gốc METS.  
- `dmdSec` có **ID**, (CREATED), (STATUS); `mdRef` có **ID**, **LOCTYPE**, **MDTYPE**, **MIMETYPE**, (CREATED), (SIZE), **CHECKSUMTYPE**, (CHECKSUM), **xlink:type**, **xlink:href**.  
- `amdSec` có **ID**; `digiprovMD` có **ID**; `mdRef` có **ID**, **LOCTYPE**, **MDTYPE**, **MIMETYPE**, (CREATED), (SIZE), **CHECKSUMTYPE**, (CHECKSUM), **xlink:type**, **xlink:href**.  
- `fileSec` có **ID**; mỗi `file` có **ID**, **MIMETYPE** (+ SIZE/CREATED/CHECKSUM/CHECKSUMTYPE nếu áp dụng); `FLocat` có **LOCTYPE**, **xlink:type**, **xlink:href**.  
- `structMap` có **ID**, **LABEL="CSIP"**; `div` cấp 1 có **ID**, **LABEL**; `div[@LABEL="Metadata"]` có **DMDID**, **ADMID**; `div[@LABEL="Schemas"]` có `<fptr FILEID>`; `div[@LABEL="Representations/rep1"]` có `<mptr xlink:href, xlink:title>`.

---

## 6) Ghi chú triển khai chương trình
- Tự động quét thư mục PDF để tính: `SIZE`, `CHECKSUM (SHA-256)`, `CREATED` (ctime/mtime), `MIMETYPE` (suy từ phần mở rộng).  
- Sinh `EAD.xml`, `PREMIS.xml` từ template; cập nhật `SIZE`/`CHECKSUM` của chính các file này vào `mdRef`.  
- Bảo đảm tất cả `@ID` là duy nhất trong phạm vi một METS; `xlink:href` dùng đường dẫn tương đối.

— **Hết** —



---

## 7) Đặc tả chi tiết **EAD.xml** (descriptive)
**Vị trí:** `AIP_hoso/metadata/descriptive/EAD.xml` — **BẮT BUỘC**.

### 7.1 Lược đồ & xác thực
- Khai báo và cung cấp ít nhất một lược đồ trong thư mục `schemas/` tương ứng với kiểu EAD áp dụng: `EAD.xsd` (tổng quát) hoặc các biến thể như `EAD_doc.xsd`, `EAD_media.xsd`, `EAD_pic.xsd`.
- Khi sinh `EAD.xml`, cần đảm bảo hợp lệ theo XSD đã chọn (kiểu dữ liệu, pattern, giá trị liệt kê…).

### 7.2 Cấu trúc dữ liệu tối thiểu (gợi ý theo XSD minh hoạ)
Các phần tử đề nghị (tối thiểu) để mô tả hồ sơ ở cấp gói AIP_hoso:
- `arcFileCode` — mã/hệ quy chiếu hồ sơ; có thể ánh xạ `HoSo.MaHoSo` hoặc mã phông + mã hồ sơ.
- `title` — tiêu đề hồ sơ; ánh xạ `HoSo.Title`.
- `maintenance` — trạng thái/sửa đổi; có thể ánh xạ `HoSo.RecordStatus` (CURRENT/REVISED…).
- `mode` — chế độ truy cập/bảo mật (nếu XSD yêu cầu); có thể ánh xạ `HoSo.DoMat`.
- `language` — ngôn ngữ; ánh xạ `HoSo.NgonNgu`.
- `startDate`, `endDate` — phạm vi thời gian; ánh xạ `HoSo.PhamViThoiGian_BD/_KT` (định dạng ISO 8601 `YYYY-MM-DD`).
- `keyword` — từ khoá (tuỳ chọn); sinh từ `HoSo.TomTat` hoặc cột riêng.
- `totalDoc`/`numberOfPaper`/`numberOfPage` — số lượng tài liệu/số tờ/số trang (tuỳ mô hình dữ liệu); có thể tính từ thư mục PDF.
- `format` — định dạng tổng quát của tập hồ sơ (ví dụ: `PDF/A` nếu áp dụng quy chuẩn).
- `inforSign` — có/không chữ ký số (tuỳ chọn; tổng hợp từ `TaiLieu.GhiChuKySo`).
- `confidenceLevel` — mức độ tin cậy (nếu XSD yêu cầu).
- `paperFileCode` — mã hồ sơ giấy (nếu có hồ sơ đối sánh).
- `description` — mô tả/tóm tắt; ánh xạ `HoSo.TomTat`.
- `riskRecovery`, `riskRecoveryStatus` — thông tin dự phòng/khôi phục rủi ro (nếu mô hình yêu cầu).

> Lưu ý: danh mục phần tử/kiểu dữ liệu phụ thuộc XSD thực tế trong `schemas/`. Khuyến nghị chốt một XSD duy nhất cho toàn bộ dự án để đảm bảo tính nhất quán.

### 7.3 Liên kết **đồng bộ** với METS & các thành phần khác
- **METS `dmdSec/mdRef`**: 
  - `@ID` = `mdref-<UUID>`; `@LOCTYPE="URL"`; `@MDTYPE="EAD"` *(hoặc `OTHER` + `OTHERMDTYPE="EAD"`)*; `@MIMETYPE="text/xml"`;
  - `@CREATED` (thời điểm sinh EAD), `@SIZE` (byte), `@CHECKSUMTYPE="SHA-256"`, `@CHECKSUM` (64 hex);
  - `xlink:type="simple"`, `xlink:href="metadata/descriptive/EAD.xml"` (đường dẫn **tương đối**).
- **METS `structMap[@LABEL="CSIP"]/div[@LABEL="Metadata"]`**:
  - Phải mang `@DMDID` tham chiếu tới `dmdSec/@ID` của EAD (ví dụ: `DMDID="dmd-…"`).
  - Nếu có `PREMIS.xml` ở cấp gói, `@ADMID` nên tham chiếu tới `amdSec/@ID` tương ứng để đảm bảo tính liên kết hồ sơ mô tả ↔ bảo quản.
- **Schemas EAD**: các file `.xsd` tương ứng phải được khai trong `fileSec/fileGrp[@USE="Schemas"]` và được trỏ tới bởi `structMap/div[@LABEL="Schemas"]/fptr@FILEID`.
- **Đồng bộ hoá dữ liệu**: các trường tổng hợp như `totalDoc`, `numberOfPage`, có thể sinh từ thực trạng tệp trong `representations/rep1/data/`. Khi thay đổi danh mục tệp, cần cập nhật lại EAD, `mdRef@SIZE/@CHECKSUM` và `structMap`.

---

## 8) Đặc tả chi tiết **PREMIS.xml** (preservation)
**Vị trí:** `AIP_hoso/metadata/preservation/PREMIS.xml` — **BẮT BUỘC**.

### 8.1 Khai báo **xmlns** & lược đồ (cập nhật theo góp ý)
Root hợp lệ ví dụ:
```xml
<premis xmlns="http://www.loc.gov/premis/v3"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xsi:schemaLocation="http://www.loc.gov/premis/v3 http://www.loc.gov/standards/premis/premis.xsd"
        version="3.0">
  ...
</premis>
```
> Có thể điều chỉnh URL lược đồ theo phiên bản PREMIS được phê duyệt trong dự án.

### 8.2 Nhóm phần tử **object** (bổ sung đầy đủ theo yêu cầu)
- **Thuộc tính**: `xmlID` *(định danh cục bộ, duy nhất trong PREMIS.xml)* — ví dụ: `xmlID="obj-file-1"`.
- **Bắt buộc tối thiểu** trong `object`:
  - `<objectIdentifier>`
    - `<objectIdentifierType>`: `LOCAL` | `UUID` | `HANDLE` … (đề xuất dùng `LOCAL`/`UUID`).
    - `<objectIdentifierValue>`: trùng với **METS `file/@ID`** (ví dụ: `file-…`) hoặc đường dẫn tương đối của tệp.
  - `<objectCategory>`: giá trị thuộc tập `{file | representation | bitstream | intellectual entity}`. 
    - Quy ước dự án: mỗi PDF → `objectCategory = file`; có thể bổ sung một `object` mức đại diện với `objectCategory = representation` cho `rep1`.
- **Đặc tả kỹ thuật đề nghị** (tối thiểu để kiểm tra tính toàn vẹn và định dạng):
  - `<objectCharacteristics>`
    - `<compositionLevel>`: `0` (thông thường cho file đơn).
    - `<fixity>` → `<messageDigestAlgorithm>SHA-256</messageDigestAlgorithm>`, `<messageDigest>` = checksum của file (64 hex).
    - `<size>`: số byte.
    - `<format>` → `<formatDesignation>/<formatName>`: ví dụ `application/pdf` (hoặc thêm `formatVersion`/`Registry` nếu có).
    - `<creatingApplication>` (tuỳ chọn nếu xác định được) → tên, phiên bản, thời điểm tạo.

**Ví dụ rút gọn (đã sửa/đủ thành phần theo góp ý):**
```xml
<premis xmlns="http://www.loc.gov/premis/v3"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xsi:schemaLocation="http://www.loc.gov/premis/v3 http://www.loc.gov/standards/premis/premis.xsd"
        version="3.0">
  <object xmlID="obj-file-1">
    <objectIdentifier>
      <objectIdentifierType>LOCAL</objectIdentifierType>
      <objectIdentifierValue>file-1D2C-AAAA...</objectIdentifierValue>
    </objectIdentifier>
    <objectCategory>file</objectCategory>
    <objectCharacteristics>
      <compositionLevel>0</compositionLevel>
      <fixity>
        <messageDigestAlgorithm>SHA-256</messageDigestAlgorithm>
        <messageDigest>4F0A...ABC</messageDigest>
      </fixity>
      <size>123456</size>
      <format>
        <formatDesignation>
          <formatName>application/pdf</formatName>
        </formatDesignation>
      </format>
      <creatingApplication>
        <creatingApplicationName>Adobe Acrobat</creatingApplicationName>
        <creatingApplicationVersion>23.0</creatingApplicationVersion>
        <dateCreatedByApplication>2025-08-20T15:22:10+07:00</dateCreatedByApplication>
      </creatingApplication>
    </objectCharacteristics>
  </object>

  <event xmlID="evt-ing-20250822-1">
    <eventIdentifier>
      <eventIdentifierType>LOCAL</eventIdentifierType>
      <eventIdentifierValue>evt-ing-20250822-1</eventIdentifierValue>
    </eventIdentifier>
    <eventType>ingestion</eventType>
    <eventDateTime>2025-08-22T09:01:00+07:00</eventDateTime>
    <eventOutcomeInformation>
      <eventOutcome>success</eventOutcome>
    </eventOutcomeInformation>
    <linkingObjectIdentifier>
      <linkingObjectIdentifierType>LOCAL</linkingObjectIdentifierType>
      <linkingObjectIdentifierValue>file-1D2C-AAAA...</linkingObjectIdentifierValue>
    </linkingObjectIdentifier>
    <linkingAgentIdentifier>
      <linkingAgentIdentifierType>SOFTWARE</linkingAgentIdentifierType>
      <linkingAgentIdentifierValue>ag-system</linkingAgentIdentifierValue>
    </linkingAgentIdentifier>
  </event>

  <agent xmlID="ag-system">
    <agentIdentifier>
      <agentIdentifierType>LOCAL</agentIdentifierType>
      <agentIdentifierValue>ag-system</agentIdentifierValue>
    </agentIdentifier>
    <agentName>Hệ thống nhập gói AIP</agentName>
    <agentType>Software</agentType>
  </agent>
</premis>
```

### 8.3 Liên kết **đồng bộ** với METS & các thành phần khác
- **METS `amdSec/digiprovMD/mdRef`**: tham chiếu tới `metadata/preservation/PREMIS.xml` với đầy đủ `@ID`, `@LOCTYPE="URL"`, `@MDTYPE="PREMIS"` *(hoặc `OTHER` + `OTHERMDTYPE="PREMIS"`)*, `@MIMETYPE="text/xml"`, `@CREATED`, `@SIZE`, `@CHECKSUMTYPE="SHA-256"`, `@CHECKSUM`, `xlink:type="simple"`, `xlink:href` tương đối.
- **METS `structMap[@LABEL="CSIP"]/div[@LABEL="Metadata"]`**: sử dụng `@ADMID` trỏ tới `amdSec/@ID` để liên hệ mô tả ↔ bảo quản ở cấp gói.
- **Ánh xạ `objectIdentifierValue` ↔ METS**: 
  - Với `objectCategory = file`: đặt `objectIdentifierValue` = **`FILEID`** (tức `mets:file/@ID`) của PDF tương ứng, giúp quy chiếu PREMIS→METS một-một.
  - Nếu bổ sung `object` mức đại diện (`representation`), có thể đặt `objectIdentifierValue = "rep1"` và dùng `linkingObjectIdentifier` trong `event` để liên kết các file thuộc đại diện.
- **Tính toàn vẹn & đồng bộ**: 
  - Khi `SIZE`/`CHECKSUM` của tệp thay đổi (do thay thế lại PDF), phải tái sinh `PREMIS.xml` **và** cập nhật `METS/file[@ID]/@SIZE/@CHECKSUM/@CHECKSUMTYPE` **và** `mdRef@SIZE/@CHECKSUM` tương ứng.

---



---

## 9) METS của bản đại diện **rep1** — `representations/rep1/METS.xml`
**Vị trí:** `AIP_hoso/representations/rep1/METS.xml` — **BẮT BUỘC** đối với bản đại diện chứa dữ liệu hồ sơ.

### 9.1 Vai trò & phạm vi
- Mô tả **cấu trúc** và **liên kết** của các tệp dữ liệu thực tế trong `rep1/data/` cùng các siêu dữ liệu cấp **tài liệu** (EAD_doc/… nếu áp dụng) và siêu dữ liệu **bảo quản ở cấp đại diện** (PREMIS_rep1.xml nếu tách riêng).
- Tối thiểu phải có: `mets` (gốc), một hoặc nhiều `dmdSec` (tham chiếu các EAD_doc_* nếu dùng), một `amdSec` (tham chiếu PREMIS_rep1.xml nếu dùng), `fileSec` (khai báo các PDF), `structMap` (tổ chức, trỏ `FILEID`).

### 9.2 Quy tắc chung
- **Namespaces** khuyến nghị: `mets`, `xlink`, `xsi`, `csip` (để dùng `csip:OAISPACKAGETYPE`, `csip:NOTETYPE`). 
- **Định danh & ID**: tất cả `@ID` là duy nhất trong phạm vi **rep1/METS.xml**; có thể dùng tiền tố `dmd-`, `amd-`, `digiprov-`, `mdref-`, `file-`, `div-`, `sm-`, `fs-`, `fg-` + UUID.
- **Đường dẫn** trong `xlink:href`: **tương đối** tính từ thư mục `rep1/` (ví dụ: `metadata/descriptive/EAD_doc_File1.xml`, `data/File1.pdf`).
- **Thời gian**: ISO 8601 `+07:00`.

### 9.3 Bảng **thuộc tính bắt buộc** theo khối (đã rà soát & bổ sung)

#### A) `<mets>` (gốc)
| Thành phần | Bắt buộc | Cardinality | Nguồn | Quy tắc/giá trị |
|---|:--:|:--:|---|---|
| `@OBJID` | **Có** | 1 | Sinh/HoSo | Định danh bản đại diện (ví dụ: `urn:uuid:<uuid-rep1>`). |
| `@TYPE` | **Có** | 1 | Cấu hình | Khuyến nghị `representation`. |
| `@PROFILE` | **Có** | 1 | Cấu hình | Theo CSIP áp dụng cho bản đại diện. |
| `csip:OAISPACKAGETYPE` | **Có** | 1 | Cấu hình | Giá trị `AIP` (gói thuộc AIP). |
| `metsHdr/@CREATEDATE` | **Có** | 1 | Sinh | ISO 8601 `+07:00`.
| `metsHdr/@LASTMODDATE` | Tuỳ | 0..1 | Sinh | Khi cập nhật. |
| `metsHdr/agent/@ROLE` | **Có** | ≥1 | Cấu hình | `CREATOR`/`ARCHIVIST`/… |
| `metsHdr/agent/@TYPE` | **Có** | ≥1 | Cấu hình | `ORGANIZATION`/`SOFTWARE`/`INDIVIDUAL` |
| `metsHdr/agent/@OTHERTYPE` | Tuỳ | 0..1 | Cấu hình | Khai nếu `TYPE="OTHER"`.
| `metsHdr/agent/name` | **Có** | ≥1 | Cấu hình | Tên cơ quan/hệ thống.
| `metsHdr/agent/note` | Tuỳ/Khuyến nghị | 0..n | Cấu hình | Cho phép ghi chú; nếu dùng `note` để ghi mã phông, **phải** đặt `csip:NOTETYPE="IDENTIFICATIONCODE"` và **giá trị** chính là **Mã phông**.

#### B) `dmdSec` (mô tả **tài liệu** — EAD_doc/EAD_media/EAD_pic … qua `mdRef`)
| Vị trí | Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|---|:--:|---|---|
| `<dmdSec>` | `@ID` | **Có** | Tự sinh | `dmd-<UUID>`.
|  | `@CREATED` | **Có** | Thời điểm sinh | ISO 8601 `+07:00`.
| `<dmdSec>/<mdRef>` | `@ID` | **Có** | Tự sinh | `mdref-<UUID>`.
|  | `@LOCTYPE` | **Có** | Cố định | `URL`.
|  | `@MDTYPE` | **Có** | Cố định | `EAD` *(hoặc `OTHER` + `OTHERMDTYPE="EAD"`)*.
|  | `@MIMETYPE` | **Có** | Cố định | `text/xml`.
|  | `@SIZE` | **Có** | Từ file | Byte size.
|  | `@CREATED` | **Có** | Thời điểm file | ISO 8601 `+07:00`.
|  | `@CHECKSUMTYPE` | **Có** | Cố định | `SHA-256`.
|  | `@CHECKSUM` | Khuyến nghị/ Có* | Tính từ file | 64 hex.
|  | `xlink:type` | **Có** | Cố định | `simple`.
|  | `xlink:href` | **Có** | Đường dẫn | Ví dụ: `metadata/descriptive/EAD_doc_File1.xml`.

> Có thể tạo 1 `dmdSec`/tài liệu hoặc 1 `dmdSec` chung cho toàn `rep1` nếu không yêu cầu mô tả chi tiết từng file.

#### C) `amdSec` (bảo quản **cấp đại diện** — PREMIS_rep1.xml qua `digiprovMD/mdRef`)
| Vị trí | Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|---|:--:|---|---|
| `<amdSec>` | `@ID` | **Có** | Tự sinh | `amd-<UUID>`.
| `<amdSec>/<digiprovMD>` | `@ID` | **Có** | Tự sinh | `digiprov-<UUID>`.
| `<amdSec>/<digiprovMD>/<mdRef>` | `@ID` | **Có** | Tự sinh | `mdref-<UUID>`.
|  | `@LOCTYPE` | **Có** | Cố định | `URL`.
|  | `@MDTYPE` | **Có** | Cố định | `PREMIS` *(hoặc `OTHER` + `OTHERMDTYPE="PREMIS"`)*.
|  | `@MIMETYPE` | **Có** | Cố định | `text/xml`.
|  | `@SIZE` | **Có** | Từ file | Byte size.
|  | `@CREATED` | **Có** | Thời điểm file | ISO 8601 `+07:00`.
|  | `@CHECKSUMTYPE` | **Có** | Cố định | `SHA-256`.
|  | `@CHECKSUM` | Khuyến nghị/ Có* | Tính từ file | 64 hex.
|  | `xlink:type` | **Có** | Cố định | `simple`.
|  | `xlink:href` | **Có** | Đường dẫn | `metadata/preservation/PREMIS_rep1.xml` (nếu tách riêng cấp đại diện).

#### D) `fileSec` (khai báo **PDF dữ liệu**)
| Vị trí | Thuộc tính | Bắt buộc | Nguồn | Quy tắc/giá trị |
|---|---|:--:|---|---|
| `<fileSec>` | `@ID` | **Có** | Tự sinh | `fs-<UUID>`.
| `<fileGrp>` | `@ID` | **Có** | Tự sinh | `fg-<UUID>`.
|  | `@USE` | **Có** | Cấu hình | Sử dụng `Data` cho nhóm dữ liệu.
| `<file>` | `@ID` | **Có** | Tự sinh | `file-<UUID>`.
|  | `@MIMETYPE` | **Có** | TaiLieu.MimeType | `application/pdf`.
|  | `@CREATED` | **Có** | Quét file | ISO 8601 `+07:00` (ctime/mtime).
|  | `@SIZE` | Khuyến nghị | Quét file | Byte size.
|  | `@CHECKSUMTYPE` | Khuyến nghị/Có* | Cố định | `SHA-256`.
|  | `@CHECKSUM` | Khuyến nghị/Có* | Quét file | 64 hex.
| `<file>/<FLocat>` | `LOCTYPE` | **Có** | Cố định | `URL`.
|  | `xlink:type` | **Có** | Cố định | `simple`.
|  | `xlink:href` | **Có** | Đường dẫn | `data/<TênFile.pdf>`.

#### E) `structMap` (tổ chức & liên kết)
| Vị trí | Thuộc tính/bộ phận | Bắt buộc | Quy tắc/giá trị |
|---|---|:--:|---|
| `<structMap>` | `@ID`, `@LABEL` | **Có** | `@LABEL="CSIP"`; `@TYPE="logical"` (khuyến nghị).
| `<div LABEL="Data">` | `@ID` | **Có** | Chứa các `div` con theo từng tài liệu.
| `<div LABEL="Data">/<div>` | `@ID`, `@LABEL` | **Có** | Mỗi tài liệu một `div` (LABEL có thể là tên file hiển thị).
| `<div LABEL="Data">/<div>/<fptr>` | `FILEID` | **Có** | **Phải** trỏ tới `mets:file/@ID` thuộc `fileGrp@USE="Data"` ứng với tài liệu.
| `<div LABEL="MetadataLink">` | `@ID` | **Có** | Nhóm liên kết **metadata ↔ file**.
| `<div LABEL="MetadataLink">/<div LABEL="MetadataLink/File">` | `@ID`, `@DMDID`, `@ADMID` | **Có** | `@ID` theo quy tắc `uuid-{UUIDS}` (UUID **IN HOA**); `@DMDID` trỏ `dmdSec/@ID` của metadata tài liệu; `@ADMID` trỏ `amdSec/@ID` (PREMIS cấp đại diện hoặc cấp tài liệu nếu có).
| `<div LABEL="MetadataLink">/<div LABEL="MetadataLink/File">/<fptr>` | `FILEID` | **Có** | Map tới `mets:file/@ID` của **chính** file tài liệu tương ứng.
| `<div LABEL="AttachmentFile">` | `@ID` | **Có** | Nhóm tệp đính kèm (nếu có).
| `<div LABEL="AttachmentFile">/<div>` | `@ID`, `@LABEL` | **Có** | Mỗi tệp đính kèm một `div`.
| `<div LABEL="AttachmentFile">/<div>/<fptr>` | `FILEID` | **Có** | Trỏ `mets:file/@ID` của tệp đính kèm.

### 9.4 Liên kết & đồng bộ với `metadata.xlsx`
- **Sheet `TaiLieu`**: mỗi dòng ↔ một `<file>` trong `fileSec` và một `div`/`fptr` tương ứng trong `structMap/Data`. Nếu sử dụng mô tả chi tiết từng tài liệu, tạo **một `dmdSec` + `mdRef`** trỏ `EAD_doc_<FileName>.xml` cho mỗi dòng.
- **PREMIS_rep1.xml** (nếu có): `objectIdentifierValue` nên trùng **`mets:file/@ID`** để liên kết PREMIS↔METS một-một; `@ADMID` tại `MetadataLink/File` giúp liên hệ bảo quản.
- Thay đổi danh mục PDF (thêm/xoá/thay) → cập nhật đồng bộ: `fileSec`, `structMap` (cả **Data**/**MetadataLink**/**AttachmentFile**), `dmdSec/mdRef`, `PREMIS_rep1.xml` và checksum tương ứng.

### 9.5 Ví dụ **đầy đủ** `rep1/METS.xml` (đã bổ sung các thuộc tính bắt buộc)
```xml
<mets:mets xmlns:mets="http://www.loc.gov/METS/"
           xmlns:xlink="http://www.w3.org/1999/xlink"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:csip="https://DILCIS.eu/XML/METS/CSIPExtensionMETS"
           OBJID="urn:uuid:11111111-2222-3333-4444-555555555555"
           TYPE="representation"
           PROFILE="CSIP-Representation-Profile">
  <csip:OAISPACKAGETYPE>AIP</csip:OAISPACKAGETYPE>
  <mets:metsHdr CREATEDATE="2025-08-22T09:05:00+07:00">
    <mets:agent ROLE="CREATOR" TYPE="SOFTWARE">
      <mets:name>RepBuilder</mets:name>
      <mets:note csip:NOTETYPE="IDENTIFICATIONCODE">MA_PHONG_ABC</mets:note>
    </mets:agent>
  </mets:metsHdr>

  <!-- dmdSec cho File1 -->
  <mets:dmdSec ID="dmd-01" CREATED="2025-08-22T09:05:01+07:00">
    <mets:mdRef ID="mdref-01" LOCTYPE="URL" MDTYPE="EAD" MIMETYPE="text/xml"
                SIZE="3456" CREATED="2025-08-22T09:05:01+07:00"
                CHECKSUMTYPE="SHA-256" CHECKSUM="A1B2..."
                xlink:type="simple" xlink:href="metadata/descriptive/EAD_doc_File1.xml"/>
  </mets:dmdSec>

  <!-- amdSec cấp đại diện (nếu áp dụng) -->
  <mets:amdSec ID="amd-01">
    <mets:digiprovMD ID="digiprov-01">
      <mets:mdRef ID="mdref-02" LOCTYPE="URL" MDTYPE="PREMIS" MIMETYPE="text/xml"
                  SIZE="5120" CREATED="2025-08-22T09:05:02+07:00"
                  CHECKSUMTYPE="SHA-256" CHECKSUM="D4E5..."
                  xlink:type="simple" xlink:href="metadata/preservation/PREMIS_rep1.xml"/>
    </mets:digiprovMD>
  </mets:amdSec>

  <mets:fileSec ID="fs-01">
    <mets:fileGrp ID="fg-data" USE="Data">
      <mets:file ID="file-01" MIMETYPE="application/pdf" CREATED="2025-08-20T15:22:10+07:00" SIZE="123456" CHECKSUMTYPE="SHA-256" CHECKSUM="4F0A...">
        <mets:FLocat LOCTYPE="URL" xlink:type="simple" xlink:href="data/File1.pdf"/>
      </mets:file>
      <mets:file ID="file-02" MIMETYPE="application/pdf" CREATED="2025-08-21T10:00:00+07:00" SIZE="234567" CHECKSUMTYPE="SHA-256" CHECKSUM="7BCD...">
        <mets:FLocat LOCTYPE="URL" xlink:type="simple" xlink:href="data/File2.pdf"/>
      </mets:file>
    </mets:fileGrp>
  </mets:fileSec>

  <mets:structMap ID="sm-01" LABEL="CSIP" TYPE="logical">
    <mets:div ID="div-data" LABEL="Data">
      <mets:div ID="div-f1" LABEL="File1">
        <mets:fptr FILEID="file-01"/>
      </mets:div>
      <mets:div ID="div-f2" LABEL="File2">
        <mets:fptr FILEID="file-02"/>
      </mets:div>
    </mets:div>

    <mets:div ID="div-metalink" LABEL="MetadataLink">
      <mets:div ID="uuid-3F8E1AB4-ABCD-4C2E-8E0C-112233445566" LABEL="MetadataLink/File" DMDID="dmd-01" ADMID="amd-01">
        <mets:fptr FILEID="file-01"/>
      </mets:div>
    </mets:div>

    <mets:div ID="div-attach" LABEL="AttachmentFile">
      <mets:div ID="att-01" LABEL="Scan_PhieuBia.pdf">
        <mets:fptr FILEID="file-02"/>
      </mets:div>
    </mets:div>
  </mets:structMap>
</mets:mets>
```

> Ghi chú: Ví dụ trên đã **bổ sung tất cả các trường bắt buộc** theo góp ý: `csip:OAISPACKAGETYPE`, `metsHdr/agent` (ROLE/TYPE/OTHERTYPE/name/note với `csip:NOTETYPE="IDENTIFICATIONCODE"`), `dmdSec@CREATED`, `mdRef@SIZE/@CREATED`, `digiprovMD/mdRef@SIZE/@CREATED`, `fileGrp@ID/@USE`, `file@CREATED`, `structMap` (ID/LABEL) và các nhánh `Data`/`MetadataLink`/`AttachmentFile` với `fptr@FILEID` trỏ đúng `mets:file/@ID`.


> Ví dụ trên lược bỏ các thuộc tính không bắt buộc để tối giản, nhưng **giữ đầy đủ các trường bắt buộc** theo yêu cầu: ID/LOCTYPE/MDTYPE/MIMETYPE/CHECKSUMTYPE/xlink:type/xlink:href ở `mdRef` & `FLocat`; `@ID` ở `fileSec`/`file`/`structMap`/`div`.

---



---

## 10) **EAD_doc_File\*.xml** — Mô tả chi tiết mức **tài liệu** trong rep1
**Vị trí:** `AIP_hoso/representations/rep1/metadata/descriptive/EAD_doc_FileN.xml` — **BẮT BUỘC** nếu dự án yêu cầu mô tả từng tài liệu; nếu không, có thể 01 EAD chung.

### 10.1 Lược đồ & yêu cầu
- Sử dụng một trong các lược đồ EAD cấp tài liệu đặt tại `AIP_hoso/schemas/` (ví dụ: `EAD_doc.xsd`, `EAD_media.xsd`, `EAD_pic.xsd`).
- `EAD_doc_FileN.xml` **phải hợp lệ** theo XSD đã chọn (kiểu dữ liệu, pattern, tập giá trị liệt kê…).

### 10.2 Tập phần tử **tối thiểu** (đề xuất theo phụ lục & XSD minh hoạ)
- `docCode` — Mã định danh tài liệu (có thể lấy từ tên tệp không phần mở rộng hoặc ID nội bộ).  
- `title` — Tiêu đề tài liệu (↔ `TaiLieu.Title`).  
- `docDate` — Ngày tài liệu (↔ `TaiLieu.NgayTaiLieu`, định dạng `YYYY-MM-DD`).  
- `language` — Ngôn ngữ (↔ `TaiLieu.NgonNgu` hoặc mặc định từ `HoSo.NgonNgu`).  
- `numberOfPage` — Số trang (↔ `TaiLieu.Trang`, nếu không có có thể bỏ qua nếu XSD không bắt buộc).  
- `format` — Định dạng/kiểu (ví dụ `application/pdf` hoặc mức `PDF/A-1b` nếu có).  
- `inforSign` — Trạng thái chữ ký số (`true|false` hoặc `0|1`) (↔ `TaiLieu.GhiChuKySo`).  
- `description` — Mô tả ngắn (nếu có).  
> Dự án có thể mở rộng thêm trường theo XSD như: `keyword`, `confidenceLevel`, `paperDocRef`… miễn đảm bảo tương thích XSD được sử dụng.

### 10.3 Liên kết **đồng bộ** với METS
- Trong `rep1/METS.xml`:
  - **`dmdSec`**: mỗi tài liệu có 01 `dmdSec` với `mdRef` trỏ tới `metadata/descriptive/EAD_doc_FileN.xml`; **bắt buộc** có `@ID`, `@LOCTYPE="URL"`, `@MDTYPE="EAD"` (hoặc `OTHER`+`OTHERMDTYPE="EAD"`), `@MIMETYPE="text/xml"`, `@SIZE`, `@CREATED`, `@CHECKSUMTYPE="SHA-256"`, `@CHECKSUM`, `xlink:type="simple"`, `xlink:href` tương đối.
  - **`structMap`**: nhánh `MetadataLink` phải có các `div LABEL="MetadataLink/File"` với `@ID=uuid-{UUIDS}` (**IN HOA**), `@DMDID` trỏ tới `dmdSec/@ID` tương ứng và `fptr@FILEID` trỏ đúng `mets:file/@ID` của **chính** tài liệu đó.

### 10.4 Ánh xạ từ `metadata.xlsx` (sheet `TaiLieu`)
`docCode` ← `FileName` (không đuôi) hoặc ID nội bộ; `title` ← `Title`; `docDate` ← `NgayTaiLieu`; `language` ← `NgonNgu?`; `numberOfPage` ← `Trang?`; `format` ← `MimeType`/mức PDF/A; `inforSign` ← `GhiChuKySo`; `description` ← cột mô tả nếu có.

### 10.5 Ví dụ rút gọn `EAD_doc_File1.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<eadDoc xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:noNamespaceSchemaLocation="../../../../schemas/EAD_doc.xsd">
  <docCode>File1</docCode>
  <title>Tờ trình phê duyệt</title>
  <docDate>2025-06-30</docDate>
  <language>vie</language>
  <numberOfPage>12</numberOfPage>
  <format>application/pdf</format>
  <inforSign>true</inforSign>
  <description>Tài liệu trình phê duyệt dự án X.</description>
</eadDoc>
```

---

## 11) **PREMIS_rep1.xml** — Bảo quản cấp **đại diện**
**Vị trí:** `AIP_hoso/representations/rep1/metadata/preservation/PREMIS_rep1.xml` — **BẮT BUỘC** nếu tách bảo quản ở cấp đại diện (ngoài PREMIS cấp gói).

### 11.1 Khai báo **xmlns** & lược đồ
```xml
<premis xmlns="http://www.loc.gov/premis/v3"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xsi:schemaLocation="http://www.loc.gov/premis/v3 http://www.loc.gov/standards/premis/premis.xsd"
        version="3.0">
  ...
</premis>
```

### 11.2 `object` mức **đại diện** (representation)
- **Thuộc tính**: `xmlID` duy nhất (ví dụ `xmlID="obj-rep1"`).
- **Bắt buộc**:
  - `objectIdentifier/objectIdentifierType` = `LOCAL` hoặc `UUID`.
  - `objectIdentifier/objectIdentifierValue` = `rep1` hoặc một UUID của đại diện.
  - `objectCategory` = `representation`.
- **Quan hệ (khuyến nghị)**: `relationship` (`relationshipType` = `structural`, `relationshipSubType` = `has part`) trỏ tới các **object file** (nếu định nghĩa trong PREMIS cấp gói) qua `relatedObjectIdentifier` (`Type` = `LOCAL|UUID`, `Value` = ID object file tương ứng). 

### 11.3 `event` tối thiểu
- `eventIdentifier` (`Type`, `Value`).
- `eventType` (ví dụ: `ingestion`, `validation`, `fixity check`).
- `eventDateTime` (ISO 8601 `+07:00`).
- `eventOutcomeInformation/eventOutcome` (ví dụ: `success`).
- **Liên kết**: `linkingObjectIdentifier` (trỏ `obj-rep1`), `linkingAgentIdentifier` (trỏ tác nhân tạo xử lý).

### 11.4 `agent` tối thiểu
- `agentIdentifier` (`Type`, `Value`).
- `agentName` (ví dụ: tên hệ thống hoặc cơ quan).
- `agentType` (ví dụ: `Software` hoặc `Organization`).

### 11.5 Liên kết **đồng bộ** với `rep1/METS.xml`
- Trong `rep1/METS.xml`, `amdSec/digiprovMD/mdRef` **bắt buộc** trỏ tới `metadata/preservation/PREMIS_rep1.xml` với đủ `@ID`, `@LOCTYPE`, `@MDTYPE`, `@MIMETYPE`, `@SIZE`, `@CREATED`, `@CHECKSUMTYPE="SHA-256"`, `@CHECKSUM`, `xlink:type`, `xlink:href`.
- `structMap/MetadataLink` dùng `@ADMID` (từ `amdSec/@ID`) để bắt cầu giữa metadata mô tả (EAD_doc) và metadata bảo quản (PREMIS_rep1) đối với từng tài liệu.
- Nếu PREMIS cấp gói đã định nghĩa `object` mức **file**, `PREMIS_rep1.xml` nên dùng `relationship` để `has part` tới các object file đó nhằm duy trì tính toàn vẹn chuỗi liên kết.

### 11.6 Ví dụ rút gọn `PREMIS_rep1.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<premis xmlns="http://www.loc.gov/premis/v3"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xsi:schemaLocation="http://www.loc.gov/premis/v3 http://www.loc.gov/standards/premis/premis.xsd"
        version="3.0">
  <object xmlID="obj-rep1">
    <objectIdentifier>
      <objectIdentifierType>LOCAL</objectIdentifierType>
      <objectIdentifierValue>rep1</objectIdentifierValue>
    </objectIdentifier>
    <objectCategory>representation</objectCategory>
    <relationship>
      <relationshipType>structural</relationshipType>
      <relationshipSubType>has part</relationshipSubType>
      <relatedObjectIdentifier>
        <relatedObjectIdentifierType>LOCAL</relatedObjectIdentifierType>
        <relatedObjectIdentifierValue>file-01</relatedObjectIdentifierValue>
      </relatedObjectIdentifier>
      <relatedObjectIdentifier>
        <relatedObjectIdentifierType>LOCAL</relatedObjectIdentifierType>
        <relatedObjectIdentifierValue>file-02</relatedObjectIdentifierValue>
      </relatedObjectIdentifier>
    </relationship>
  </object>

  <event xmlID="evt-rep1-ing-20250822">
    <eventIdentifier>
      <eventIdentifierType>LOCAL</eventIdentifierType>
      <eventIdentifierValue>evt-rep1-ing-20250822</eventIdentifierValue>
    </eventIdentifier>
    <eventType>ingestion</eventType>
    <eventDateTime>2025-08-22T09:10:00+07:00</eventDateTime>
    <eventOutcomeInformation><eventOutcome>success</eventOutcome></eventOutcomeInformation>
    <linkingObjectIdentifier>
      <linkingObjectIdentifierType>LOCAL</linkingObjectIdentifierType>
      <linkingObjectIdentifierValue>rep1</linkingObjectIdentifierValue>
    </linkingObjectIdentifier>
    <linkingAgentIdentifier>
      <linkingAgentIdentifierType>SOFTWARE</linkingAgentIdentifierType>
      <linkingAgentIdentifierValue>ag-rep-builder</linkingAgentIdentifierValue>
    </linkingAgentIdentifier>
  </event>

  <agent xmlID="ag-rep-builder">
    <agentIdentifier>
      <agentIdentifierType>LOCAL</agentIdentifierType>
      <agentIdentifierValue>ag-rep-builder</agentIdentifierValue>
    </agentIdentifier>
    <agentName>RepBuilder</agentName>
    <agentType>Software</agentType>
  </agent>
</premis>
```

---



---

## 12) ÁNH XẠ THỰC TẾ TỪ `metadata.xlsx` → AIP_hoso (đúng Phụ lục I – TT 05/2025)
**Tệp đã phân tích:** `/mnt/data/metadata.xlsx` (Sheet: `Sheet1`). Cấu trúc đúng mô tả của anh/chị:
- **Khối Hồ sơ**: cột **B → X** *(2→24)*
- **Khối Tài liệu**: cột **Y → AT** *(25→46)*; trong đó **AT = “Đường dẫn file”** tới PDF.
### 12.A Quy tắc dự án — Trích xuất mã từ tên file & mặc định điền dữ liệu
**1. Trích xuất mã từ tên file (cột AT – “Đường dẫn file”**)
**Quy tắc**: [Mã hồ sơ].[Số thứ tự văn bản].pdf
- arcFileCode (mã hồ sơ) = phần trước dấu chấm cuối cùng
- Số thứ tự = phần sau dấu chấm cuối cùng
- Mã lưu trữ tài liệu = tên file không phần mở rộng

Đã gắn vào:
EAD.xml/arcFileCode = giá trị trích;
EAD.xml/paperFileCode = arcFileCode (theo yêu cầu của anh/chị);
EAD_doc_File*.xml/docCode = Mã lưu trữ tài liệu;
rep1/METS.xml → FLocat@xlink:href = data/<tên-tệp>.pdf.

**2. Mặc định “Mức độ tin cậy”**
confidenceLevel trong EAD.xml (và EAD_doc nếu XSD có) mặc định Số hóa.
**3. Ràng buộc kiểm tra & đồng bộ**
- Số thứ tự rút từ tên file phải trùng cột “Số thứ tự văn bản trong hồ sơ”.
- Tất cả dòng thuộc cùng một hồ sơ phải có arcFileCode giống nhau.
- Khuyến nghị thêm một objectIdentifier phụ trong PREMIS (Type = LOCAL_FILENAME) mang Mã lưu trữ tài liệu để tra cứu, ngoài định danh gắn mets:file/@ID.

### 12.1 Danh mục cột nhận diện (đã đọc từ file mẫu)
**Hồ sơ (B→X):** `Phông`, `Mục lục`, `Hộp số`, `Số và ký hiệu hồ sơ`, `Tiêu đề hồ sơ`, `Thời hạn bảo quản`, `Chế độ sử dụng`, `Ngôn ngữ`, `Ngày bắt đầu`, `Tháng bắt đầu`, `Năm bắt đầu`, `Ngày kết thúc`, `Tháng kết thúc`, `Năm kết thúc`, `Tổng số văn bản trong hồ sơ`, `Chú giải`, `Ký hiệu thông tin`, `Từ khóa`, `Số lượng tờ`, `Tình trạng vật lý`, `Mức độ tin cậy`, `Mã hồ sơ giấy gốc ( nếu có )`, `Ghi chú`.

**Tài liệu (Y→AT):** `Số thứ tự văn bản trong hồ sơ`, `Tên loại văn bản`, `Số của văn bản`, `Ký hiệu của văn bản`, `Ngày văn bản`, `Tháng văn bản`, `Năm văn bản`, `Tên cơ quan, tổ chức ban hành văn bản`, `Trích yếu nội dung`, `Ngôn ngữ.1`, `Số lượng trang của văn bản`, `Ghi chú.1`, `Ký hiệu thông tin.1`, `Từ khóa.1`, `Chế độ sử dụng.1`, `Mức độ tin cậy.1`, `Bút tích`, `Tình trạng vật lý.1`, `Quy trình xử lý ( nếu có )`, `Tờ số`, `Loại tài liệu`, `Đường dẫn file`.

> Ghi chú: các cột còn lại như `STT` (A) chỉ dùng nội bộ/kiểm soát, không ánh xạ ra METS/EAD/PREMIS.

### 12.2 Ánh xạ **khối Hồ sơ** (B→X) → `AIP_hoso/METS.xml` + `AIP_hoso/metadata/descriptive/EAD.xml`
| Cột Excel | Mục đích | Nơi đưa vào AIP | Quy tắc/Chuẩn hoá |
|---|---|---|---|
| **Phông** | Mã/tên phông | `metsHdr/agent/note` với `csip:NOTETYPE="IDENTIFICATIONCODE"` | Ghi đúng **Mã phông**; nếu là tên phông, có thể thêm mã trong ngoặc. |
| **Mục lục**, **Hộp số** | Thông tin vị trí vật mang | `EAD.xml` (`paperFileCode`) | Ghép `Mục lục-Hộp số` hoặc theo quy ước kho. |
| **Số và ký hiệu hồ sơ** | Định danh hồ sơ | `EAD.xml` (`arcFileCode` hoặc `unitid` tương đương) | Chuẩn hoá không dấu/khoảng trắng nếu dùng trong URI. |
| **Tiêu đề hồ sơ** | Nhãn/tiêu đề | `mets/@LABEL` & `EAD.xml/title` | Giữ nguyên tiếng Việt có dấu. |
| **Thời hạn bảo quản** | Thuộc tính lưu trữ | `EAD.xml/maintenance` (hoặc `retention` nếu XSD có) | Ví dụ: `Vĩnh viễn`, `20 năm`… |
| **Chế độ sử dụng** | Hạn chế truy cập | `EAD.xml/mode` | Quy ước: `Công khai`/`Hạn chế`/`Mật`… |
| **Ngôn ngữ** | Ngôn ngữ hồ sơ | `EAD.xml/language` | Chuẩn ISO 639-3: `vie` cho "Tiếng Việt" (khuyến nghị). |
| **Ngày/Tháng/Năm bắt đầu**, **kết thúc** | Phạm vi thời gian | `EAD.xml/startDate`, `endDate` | Hợp nhất thành ISO `YYYY-MM-DD`. Nếu thiếu ngày → dùng `01`. |
| **Tổng số văn bản trong hồ sơ** | Số lượng tài liệu | `EAD.xml/totalDoc` | Có thể tính lại từ dữ liệu tài liệu (Y→AT). |
| **Từ khóa** | Tra cứu | `EAD.xml/keyword` | Tách bằng dấu `;`. |
| **Số lượng tờ** | Thống kê vật lý | `EAD.xml/numberOfPaper` | Nếu có thêm `numberOfPage`, nêu rõ ngữ nghĩa khác biệt. |
| **Tình trạng vật lý** | Mô tả trạng thái | `EAD.xml/description` (hoặc trường chuyên biệt nếu XSD có) | Ngắn gọn. |
| **Mức độ tin cậy** | Độ tin cậy | `EAD.xml/confidenceLevel` | Dùng giá trị số/tập liệt kê của XSD. |
| **Mã hồ sơ giấy gốc ( nếu có )** | Liên kết hồ sơ giấy | `EAD.xml/paperFileCode` | Không bắt buộc, khuyến nghị nếu có. |
| **Chú giải/Ghi chú** | Ghi chú | `EAD.xml/description` | Gộp nếu cần. |

**Bổ sung kỹ thuật bắt buộc:**
- `AIP_hoso/METS.xml` phải có: `@OBJID` (UUID), `@TYPE="AIP"`, `csip:OAISPACKAGETYPE=AIP`, `metsHdr/@CREATEDATE`, `metsHdr/agent {ROLE,TYPE, name}`, `structMap/LABEL="CSIP"` (đã mô tả ở các mục 1, 7, 9).
- `dmdSec/mdRef` trỏ tới `metadata/descriptive/EAD.xml` với **`@ID, @LOCTYPE, @MDTYPE, @MIMETYPE, @SIZE, @CREATED, @CHECKSUMTYPE, @CHECKSUM, xlink:type, xlink:href`**.

### 12.3 Ánh xạ **khối Tài liệu** (Y→AT) → `rep1/METS.xml` + `EAD_doc_File*.xml`
| Cột Excel | Mục đích | Nơi đưa vào AIP | Quy tắc/Chuẩn hoá |
|---|---|---|---|
| **Số thứ tự văn bản trong hồ sơ** | Thứ tự hiển thị | `structMap/div[@LABEL="Data"]/div` (thứ tự), `div/@LABEL` | Dùng để sắp xếp `File1, File2…` |
| **Tên loại văn bản**, **Số của văn bản**, **Ký hiệu của văn bản**, **Trích yếu nội dung** | Tiêu đề/nhận diện | `EAD_doc_FileN.xml/title` (hoặc ghép: "[Loại] số [Số]/[Ký hiệu] – [Trích yếu]") | Chuẩn hoá bỏ khoảng trắng thừa, giữ dấu. |
| **Ngày/Tháng/Năm văn bản** | Ngày ban hành | `EAD_doc_FileN.xml/docDate` | Hợp nhất thành ISO `YYYY-MM-DD` (thiếu ngày → `01`). |
| **Tên cơ quan, tổ chức ban hành văn bản** | Tác giả/cơ quan ban hành | `EAD_doc_FileN.xml/origination` (nếu XSD hỗ trợ) | Giữ nguyên. |
| **Ngôn ngữ.1** | Ngôn ngữ tài liệu | `EAD_doc_FileN.xml/language` | Chuẩn ISO 639-3 nếu có thể. |
| **Số lượng trang của văn bản** | Thống kê | `EAD_doc_FileN.xml/numberOfPage` | Nếu rỗng có thể suy từ PDF khi xử lý. |
| **Từ khóa.1`/`Ký hiệu thông tin.1`/`Chế độ sử dụng.1`/`Mức độ tin cậy.1`/`Bút tích`/`Tình trạng vật lý.1`/`Quy trình xử lý ( nếu có )`/`Tờ số`/`Loại tài liệu`** | Thuộc tính bổ sung | Trường tương ứng trong EAD_doc (nếu XSD có) | Không bắt buộc → đưa khi có dữ liệu & XSD hỗ trợ. |
| **Đường dẫn file (AT)** | Định vị tệp PDF | `rep1/METS.xml` → `fileSec/file/FLocat@xlink:href` | Chuẩn hoá đường dẫn **tương đối**: `data/<basename>.pdf`. Lưu ý đổi `\`→`/`.

**Bắt buộc tại `rep1/METS.xml`:**
- `dmdSec` **mỗi tài liệu 1 mục** (nếu mô tả chi tiết), `mdRef` với đủ `@SIZE`, `@CREATED`, `@CHECKSUMTYPE`, `@CHECKSUM`.
- `fileSec/file` **mỗi PDF 1 mục**: `@ID`, `@MIMETYPE="application/pdf"`, `@CREATED` (lấy từ mtime file), (khuyến nghị `@SIZE`, `@CHECKSUMTYPE/@CHECKSUM`). `FLocat{LOCTYPE="URL", xlink:type="simple", xlink:href}`.
- `structMap` có 3 nhánh như mục 9: **Data** (liệt kê tệp), **MetadataLink** (liệt kê cặp *metadata ↔ file*), **AttachmentFile** (nếu có tệp đính kèm). Trong `MetadataLink/File`: `@ID=uuid-{UUIDS}` (**IN HOA**), `@DMDID` trỏ `dmdSec/@ID`, `@ADMID` trỏ `amdSec/@ID`, và `<fptr FILEID="file-…">` trỏ đúng tệp.

### 12.4 Liên kết với **PREMIS** (cấp gói & cấp đại diện)
- **Cấp gói (`AIP_hoso/metadata/preservation/PREMIS.xml`)**: tạo `object` cho **từng file** PDF (objectCategory=`file`) với `objectIdentifierValue = mets:file/@ID`, `fixity SHA-256`, `size`, `format`. Các `event`: `ingestion`, `fixity check`… liên kết qua `linkingObjectIdentifier`.
- **Cấp đại diện (`rep1/.../PREMIS_rep1.xml`)**: tạo `object` (objectCategory=`representation`, id=`rep1`) **has part** tới các object file; có `event` tại cấp đại diện; `agent` là phần mềm/cơ quan xử lý.
- **`rep1/METS.xml` → `amdSec/digiprovMD/mdRef`**: trỏ tới `PREMIS_rep1.xml` với đủ `@SIZE`, `@CREATED`, `@CHECKSUMTYPE`, `@CHECKSUM`.

### 12.5 Quy tắc đồng bộ & phát sinh ID/OBJID
- **OBJID gói**: sinh `urn:uuid:{UUID}` cho `AIP_hoso/METS.xml`. Tên thư mục gói thay `:` → `_`.
- **ID con**: `dmd-<UUID>`, `amd-<UUID>`, `digiprov-<UUID>`, `mdref-<UUID>`, `file-<UUID>`, `div-<UUID>`, `sm-<UUID>`, `fs-<UUID>`, `fg-<UUID>`…
- **Chuẩn hoá ngày**: hợp nhất (ngày/tháng/năm) → ISO 8601; nếu thiếu ngày, đặt `01` và ghi chú ở `EAD_doc` (nếu cần). 
- **Ngôn ngữ**: map `"Tiếng Việt"` → `vie`; có thể mở bảng ánh xạ cho ngôn ngữ khác.
- **Đường dẫn tệp**: luôn chuyển thành **tương đối** trong gói (`representations/rep1/data/…`).
- **Liên kết PREMIS↔METS**: bắt buộc `objectIdentifierValue = mets:file/@ID` để tra chéo.

### 12.6 Ví dụ ánh xạ **hàng dữ liệu đầu tiên** (rút gọn)
- **Hồ sơ**: 
  - `Tiêu đề hồ sơ` → `mets/@LABEL` & `EAD/title` = "Tập lưu văn bản đi…"
  - `Phông` → `metsHdr/agent/note@csip:NOTETYPE="IDENTIFICATIONCODE"` = *MA_PHONG/Chi cục ATTP…*
  - `Ngày/Tháng/Năm bắt đầu`=1/1/2010, `kết thúc`=28/6/2010 → `startDate=2010-01-01`, `endDate=2010-06-28`
- **Tài liệu** (STT VB=1):
  - Tiêu đề EAD_doc = "Quyết định số 01/ QĐ-CCATVSTP – Quyết định Về việc ban hành Quy chế chi tiêu nội bộ…"
  - `docDate` = `2010-01-01`; `language` = `vie`.
  - `FLocat@xlink:href` = `data/001.03.08.H30.81.2024.K4.01.01.001.pdf`.
  - `dmdSec/mdRef` trỏ `metadata/descriptive/EAD_doc_File1.xml` (ghi `SIZE/CREATED/CHECKSUM*`).
  - `structMap/MetadataLink/File` có `@DMDID="dmd-…"`, `@ADMID="amd-…"`, và `<fptr FILEID="file-…">` đúng với PDF.

### 12.7 Khoảng thiếu & khuyến nghị bổ sung cột (nếu muốn tự quản trị)
- **OBJID gói** (nếu muốn kiểm soát thay vì tự sinh UUID).
- **RecordStatus** (`NEW|SUPPLEMENT|DELETE`) cho `metsHdr/@RECORDSTATUS`.
- **Ghi chú chữ ký số** (`GhiChuKySo`) để điền `EAD_doc/inforSign` & đánh dấu PREMIS `event validation`.
- **Ngôn ngữ mã hoá** riêng (ISO 639-3) nếu cần đầu ra chuẩn quốc tế.

> Với ánh xạ này, đội dev có thể triển khai ngay bộ chuyển đổi `metadata.xlsx` → `AIP_hoso` đảm bảo **đủ trường bắt buộc** của METS/EAD/PREMIS và **liên kết 1–1–n** giữa *Hồ sơ ↔ Tài liệu ↔ Tệp PDF*.



---

## 12.A Quy tắc dự án — Trích xuất mã từ tên file & mặc định điền dữ liệu
**Áp dụng cho file Excel hiện tại (cột AT = “Đường dẫn file”).**

### A.1 Quy tắc tên file & trích xuất mã
- Quy tắc tên file PDF: `[Mã hồ sơ].[Số thứ tự văn bản trong hồ sơ].pdf`.
- Thuật toán trích xuất từ `AT`:
  1) Lấy **tên tệp** (bỏ đường dẫn), bỏ phần mở rộng `.pdf`.
  2) Tách tại **dấu chấm cuối cùng**:
     - **arcFileCode** (mã hồ sơ) = phần **trước** dấu chấm cuối cùng.
     - **Số thứ tự văn bản** = phần **sau** dấu chấm cuối cùng (chỉ chứa chữ số).
     - **Mã lưu trữ tài liệu** = **tên tệp không phần mở rộng** (toàn bộ chuỗi trước khi thêm `.pdf`).
- Ví dụ: `001.03.08.H30.81.2024.K4.01.01.001.pdf` ⇒
  - `arcFileCode` = `001.03.08.H30.81.2024.K4.01.01`
  - `Số thứ tự` = `001`
  - `Mã lưu trữ tài liệu` = `001.03.08.H30.81.2024.K4.01.01.001`

### A.2 Gán vào các trường của AIP_hoso
- **EAD.xml (cấp hồ sơ)**:
  - `arcFileCode` = giá trị trích từ tên file (A.1)
  - `paperFileCode` = **bằng** `arcFileCode` (theo yêu cầu dự án)
  - `confidenceLevel` = **mặc định** `Số hóa`
- **EAD_doc_File*.xml (cấp tài liệu)**:
  - `docCode` = **Mã lưu trữ tài liệu** (A.1)
  - (Nếu XSD có trường `confidenceLevel`) đặt **mặc định** `Số hóa`
- **rep1/METS.xml**:
  - `fileSec/file/FLocat@xlink:href` = `data/<tên-tệp>.pdf` (đường dẫn tương đối)
  - `structMap/MetadataLink/div[@LABEL="MetadataLink/File"]/fptr@FILEID` trỏ đúng `file/@ID` của PDF tương ứng
- **PREMIS (cấp gói và/hoặc cấp đại diện)**:
  - Với mỗi file PDF (objectCategory = `file`), ngoài `objectIdentifier` gắn với `mets:file/@ID`, **khuyến nghị** thêm một `objectIdentifier` phụ (Type: `LOCAL_FILENAME`) có giá trị = **Mã lưu trữ tài liệu** để thuận tiện tra cứu.

### A.3 Ràng buộc kiểm tra dữ liệu
- `Số thứ tự` rút ra từ tên file **phải bằng** cột **“Số thứ tự văn bản trong hồ sơ”**; nếu khác → ghi log cảnh báo.
- Tất cả dòng thuộc **cùng một hồ sơ** phải có `arcFileCode` **giống nhau**.
- `FLocat@xlink:href` phải đúng **tên tệp**; nếu Excel cung cấp đường dẫn tuyệt đối hoặc dùng dấu `\`, hệ thống cần chuẩn hoá sang tương đối và dấu `/`.

> Các quy tắc A.1–A.3 **ghi đè** các mô tả chung trước đó ở mục 12 cho **dự án này**.

