Dưới đây là **bản thiết kế chương trình Python** để chuyển đổi `metadata.xlsx` + PDF thành các gói **AIP\_hoso** đúng Phụ lục I Thông tư 05/2025/TT-BNV. Tôi bám sát tài liệu mô tả “aip\_hoso\_mets\_rtm\_v\_1\_0\_tt\_05\_2025\_tt\_bnv.md” anh/chị cung cấp (quy định cấu trúc gói AIP, METS gốc/rep1, EAD, PREMIS, ánh xạ Excel).&#x20;

---

# 1) Mục tiêu & phạm vi

* Sinh gói **AIP\_hoso** (đúng OAIS/CSIP) cho từng hồ sơ; mỗi hồ sơ là một file nén riêng, đồng thời có thư mục AIP tương ứng (giữ/xoá theo lựa chọn).&#x20;
* Gói chứa: `METS.xml` (gốc), `metadata/descriptive/EAD.xml`, `metadata/preservation/PREMIS.xml`, thư mục `representations/rep1` (METS của rep1 + PDF), `schemas/` (XSD), `documentation/` (tuỳ chọn).&#x20;

---

# 2) Tham số vào/ra & cách chạy

## 2.1. Input (CLI hoặc hỏi tương tác)

* `--meta` (đường dẫn Excel): mặc định `data\input\metadata.xlsx`
* `--pdf-root` (thư mục gốc PDF): mặc định `data\input\PDF_Files`
* `--out` (thư mục đầu ra): mặc định `data\output_[yyyyMMdd_HHmmss]`
* `--keep-folders` (Y/n): mặc định `Y` (giữ thư mục AIP sau khi nén)

Ví dụ:

```bash
python -m aip_builder build ^
  --meta "data\input\metadata.xlsx" ^
  --pdf-root "data\input\PDF_Files" ^
  --out "data\output_20250823_0100" ^
  --keep-folders Y
```

## 2.2. Output

* Mỗi hồ sơ → một thư mục `AIP_hoso/<OBJID_đã_chuyển_đổi>` + một file nén `.zip` tương ứng, đặt đúng cấu trúc thư mục phản chiếu từ `pdf-root` (giữ nguyên cây thư mục tương đối của hồ sơ gốc).&#x20;
* Đường dẫn trong METS **tương đối** so với gói AIP.&#x20;

---

# 3) Luồng xử lý (pipeline)

1. **Đọc `metadata.xlsx`** (pandas/openpyxl).

   * Khối **Hồ sơ**: cột **B→X**; Khối **Tài liệu**: cột **Y→AT**, trong đó **AT** = “Đường dẫn file”.&#x20;
2. **Chuẩn hoá & nhóm hồ sơ**

   * Quy ước dự án: **tất cả PDF trong cùng một thư mục** (con của `pdf-root`) thuộc **1 hồ sơ**. Kiểm tra chéo với mã hồ sơ trích từ tên tệp (mục 4).
3. **Trích thông tin PDF**: kích thước (byte), thời gian tạo/sửa (mtime), **SHA-256** (fixity), số trang (PyPDF2).&#x20;
4. **Sinh EAD.xml** (cấp hồ sơ) từ template/XSD đã chọn; điền thống kê/từ khoá/ngôn ngữ/phạm vi thời gian…&#x20;
5. **Sinh PREMIS.xml** (cấp gói): tạo `object` cho **mỗi file PDF** (category=`file`), kèm `fixity`, `size`, `format`; tạo `event` (`ingestion`, `fixity check`) và `agent`.&#x20;
6. **Sinh METS gốc**: `metsHdr` (CREATEDATE, agent), `dmdSec/mdRef` → EAD.xml, `amdSec/digiprovMD/mdRef` → PREMIS.xml, `fileSec`, `structMap` (nhánh `Metadata`, `Schemas`, `Representations/rep1`). Bắt buộc có `csip:OAISPACKAGETYPE=AIP`.&#x20;
7. **Sinh `rep1/METS.xml`**: dmdSec (EAD\_doc\_\* từng tài liệu nếu áp dụng), amdSec (PREMIS\_rep1 nếu tách), `fileSec` (PDF), `structMap` (nhánh `Data`, `MetadataLink`, `AttachmentFile`).&#x20;
8. **Đóng gói**: copy `schemas/` chuẩn; nén thư mục AIP\_hoso thành `.zip`; xử lý `--keep-folders`.&#x20;
9. **Kiểm tra hợp lệ tối thiểu**: đủ trường bắt buộc trong `mdRef`, `FLocat`, `file`, `structMap`, `csip:OAISPACKAGETYPE`, checksum SHA-256.&#x20;

---

# 4) Quy tắc ánh xạ dữ liệu & chuẩn hoá

## 4.1. Từ tên file PDF (cột **AT**)

* Quy tắc: `[Mã hồ sơ].[Số thứ tự văn bản].pdf`
* Trích xuất:

  * `arcFileCode` = phần **trước** dấu chấm cuối cùng,
  * `STT` = phần **sau** dấu chấm cuối cùng (digits),
  * `docCode` (mã lưu trữ tài liệu) = tên file **không** đuôi `.pdf`.
* **Mặc định**: `confidenceLevel = "Số hóa"` (cấp hồ sơ & tài liệu nếu XSD có).
* **Ràng buộc**: `STT` trích ra **=** cột “Số thứ tự văn bản trong hồ sơ”; tất cả dòng cùng thư mục phải có cùng `arcFileCode`.&#x20;

## 4.2. Ánh xạ **khối Hồ sơ** (B→X) → `AIP_hoso/METS.xml` + `EAD.xml`

* `Tiêu đề hồ sơ` → `mets/@LABEL`, `EAD/title`
* `Phông` → `metsHdr/agent/note@csip:NOTETYPE="IDENTIFICATIONCODE"`
* `Ngày/Tháng/Năm BD/KT` → `EAD/startDate`, `EAD/endDate` (ISO `YYYY-MM-DD`; thiếu ngày → `01`)
* `Ngôn ngữ` → `EAD/language` (khuyến nghị ISO 639-3 `vie`)
* `Số lượng tờ`, `Từ khoá`, `Chế độ sử dụng`, `Thời hạn bảo quản`, `Tình trạng vật lý`, `Mã hồ sơ giấy` … → các phần tử EAD tương ứng (theo XSD đã chọn).&#x20;

## 4.3. Ánh xạ **khối Tài liệu** (Y→AT) → `rep1/METS.xml` + `EAD_doc_*`

* `Tên loại văn bản`/`Số`/`Ký hiệu`/`Trích yếu` → `EAD_doc/title` (có thể ghép)
* `Ngày/Tháng/Năm văn bản` → `EAD_doc/docDate` (ISO)
* `Ngôn ngữ.1`, `Số trang`, `Cơ quan ban hành`, `Từ khoá.1`… → trường EAD\_doc tương ứng nếu XSD hỗ trợ
* `Đường dẫn file` → `rep1/METS.xml` → `file/FLocat@xlink:href = data/<basename>.pdf` (đường dẫn **tương đối**, `/` separator).&#x20;

---

# 5) Ràng buộc kỹ thuật METS/EAD/PREMIS (phần bắt buộc)

* **METS gốc**: có `@OBJID` (URN UUID), `@TYPE` (AIP), `metsHdr/agent{ROLE,TYPE,name}`, `csip:OAISPACKAGETYPE=AIP`; `dmdSec/mdRef` (EAD.xml) & `amdSec/digiprovMD/mdRef` (PREMIS.xml) phải có `@ID`, `@LOCTYPE="URL"`, `@MDTYPE`, `@MIMETYPE`, `@SIZE`, `@CREATED`, `@CHECKSUMTYPE="SHA-256"`, `@CHECKSUM`, `xlink:type="simple"`, `xlink:href` **tương đối**.&#x20;
* **fileSec/FLocat**: `file/@ID`, `@MIMETYPE="application/pdf"`, (khuyến nghị `@SIZE`, `@CREATED`, `@CHECKSUMTYPE/@CHECKSUM`); `FLocat{LOCTYPE="URL", xlink:type="simple", xlink:href}`.&#x20;
* **structMap**: `@ID`, `@LABEL="CSIP"`, `div` cấp 1 cho `Metadata` (gắn `DMDID`/`ADMID`), `Schemas` (fptr→XSD), `Representations/rep1` (mptr→`rep1/METS.xml`).&#x20;
* **rep1/METS.xml**: dmdSec (EAD\_doc\_\*), amdSec (PREMIS\_rep1 nếu tách), `fileSec` nhóm `USE="Data"`, `structMap` với nhánh `Data`, `MetadataLink` (mỗi file: `div LABEL="MetadataLink/File" DMDID=…, ADMID=… + fptr@FILEID`), `AttachmentFile` (nếu có).&#x20;
* **PREMIS**: cấp gói — `object(file)` với fixity SHA-256; **liên kết** PREMIS↔METS qua `objectIdentifierValue = mets:file/@ID`; cấp đại diện (nếu có) — `object(representation)` `has part` các `object(file)`.&#x20;

---

# 6) Kiến trúc mã nguồn (đề xuất)

```
aip_builder/
  __main__.py            # CLI (click/typer)
  config.py              # mặc định & đọc cấu hình
  excel_reader.py        # parse metadata.xlsx (B→X, Y→AT)
  grouping.py            # nhóm hồ sơ theo thư mục + arcFileCode
  pdf_probe.py           # size, mtime, sha256, page_count
  models.py              # Pydantic: HoSo, TaiLieu, FileInfo, PackagePlan
  templates/
    ead.xml.j2
    ead_doc.xml.j2
    premis.xml.j2
    premis_rep1.xml.j2
    mets_root.xml.j2
    mets_rep1.xml.j2
  xml_builders.py        # render bằng lxml/jinja2 + tính SIZE/CHECKSUM
  package_writer.py      # tạo cây thư mục AIP + copy schemas + ghi file
  zipper.py              # nén từng AIP, xử lý keep-folders
  validator.py           # checklist bắt buộc/nhật ký cảnh báo
  utils/pathlib_win.py   # hỗ trợ đường dẫn dài Windows (\\?\)
  schemas/               # METS.xsd, EAD*.xsd, PREMIS.xsd (bản kèm dự án)
```

**Thư viện đề xuất:** `pandas`, `openpyxl`, `lxml`, `jinja2`, `PyPDF2`, `click`/`typer`, `pydantic`, `tqdm`.

---

# 7) Logic then chốt

## 7.1 Nhóm hồ sơ & đối chiếu

* **Nhóm chính theo thư mục con** bên trong `pdf-root` (mỗi thư mục = 1 hồ sơ).
* **Đối chiếu arcFileCode** trích từ tên PDF trong thư mục: nếu xuất hiện **>1 arcFileCode** → **cảnh báo/stop** (vi phạm quy ước “một thư mục = một hồ sơ”).
* Thứ tự tài liệu dùng `STT` trong tên tệp/Excel; lệch → ghi cảnh báo (không chặn).

## 7.2 Sinh ID & OBJID

* `OBJID` gói: `urn:uuid:{UUID4}` → tên thư mục gói = thay `:` bằng `_`.&#x20;
* ID thành phần: tiền tố `dmd-`, `amd-`, `digiprov-`, `mdref-`, `file-`, `div-`, `sm-`, `fs-`, `fg-` + UUID **duy nhất trong từng METS**.&#x20;

## 7.3 Xây EAD.xml (cấp hồ sơ)

* Điền `arcFileCode`, `paperFileCode` (bằng `arcFileCode`), `language`, phạm vi thời gian, `totalDoc`, `numberOfPaper`, `description`, `confidenceLevel="Số hóa"`.&#x20;

## 7.4 Xây PREMIS.xml (cấp gói)

* Mỗi PDF → một `object(file)` với `fixity SHA-256`, `size`, `format`; tạo `event ingestion/fixity check` + `agent` phần mềm. **`objectIdentifierValue` = `mets:file/@ID`** để liên kết PREMIS↔METS.&#x20;

## 7.5 METS gốc

* `metsHdr` (CREATEDATE + agent {ROLE,TYPE,name}); `dmdSec/mdRef` EAD.xml; `amdSec/digiprovMD/mdRef` PREMIS.xml (đủ `@SIZE`, `@CREATED`, `@CHECKSUMTYPE/@CHECKSUM`).
* `fileSec` khai báo XSD trong `schemas/` và tệp khác (nếu đính kèm), nhóm theo `fileGrp@USE`.
* `structMap` có nhánh `Metadata` (gắn `DMDID`/`ADMID`), `Schemas` (fptr), `Representations/rep1` (mptr → `rep1/METS.xml`).&#x20;

## 7.6 METS của `rep1`

* `fileGrp@USE="Data"`: mỗi PDF một `<file>` với `FLocat@xlink:href="data/<file>.pdf"`.
* `dmdSec` cho **từng tài liệu** (EAD\_doc\_\*), hoặc 1 dmdSec chung nếu không yêu cầu mô tả chi tiết (mặc định đề xuất: **mỗi tài liệu một dmdSec**).
* `structMap` gồm:

  * `Data`: liệt kê từng tài liệu và `<fptr FILEID="file-...">`
  * `MetadataLink`: với `div LABEL="MetadataLink/File" DMDID=..., ADMID=...` + fptr tới đúng `FILEID`
  * `AttachmentFile`: nếu có tệp kèm.&#x20;

---

# 8) Hỗ trợ đường dẫn dài Windows

* Dùng `pathlib` + tiền tố `\\?\` cho mọi thao tác file/zip khi chiều dài > 240 ký tự; chuẩn hoá phân tách về `/` trong **METS**.
* Khi đọc Excel và quét PDF, luôn lưu **đường dẫn tương đối trong gói** để ghi vào `xlink:href`.&#x20;

---

# 9) Kiểm tra hợp lệ & nhật ký

* **Checklist tối thiểu**: có `csip:OAISPACKAGETYPE=AIP`; `mdRef` đủ `ID/LOCTYPE/MDTYPE/MIMETYPE/SIZE/CREATED/CHECKSUMTYPE/(CHECKSUM)/xlink:type/xlink:href`; `FLocat` đủ `LOCTYPE/xlink:type/xlink:href`; `structMap` có `LABEL="CSIP"` và nhánh bắt buộc; **ID** không trùng trong cùng METS.&#x20;
* **Cảnh báo**: lệch STT, PDF thiếu, checksum lỗi, trộn `arcFileCode` trong cùng thư mục, thiếu trường tối thiểu EAD/PREMIS.
* Xuất `report.csv` và `process.log` theo hồ sơ.

---

# 10) Khung dữ liệu (Pydantic — rút gọn)

```python
class TaiLieu(BaseModel):
    stt: int
    title: str
    doc_date: date | None
    filename: str                # basename.pdf
    rel_href: str                # representations/rep1/data/<basename>.pdf
    size: int
    mtime: datetime
    sha256: str
    pages: int | None

class HoSo(BaseModel):
    arc_file_code: str
    title: str
    language: str = "vie"
    start_date: date | None
    end_date: date | None
    paper_file_code: str | None  # = arc_file_code (yêu cầu dự án)
    confidence_level: str = "Số hóa"
    keywords: list[str] = []
    number_of_paper: int | None
    notes: str | None
    tai_lieu: list[TaiLieu] = []
```

---

# 11) Pseudo-code các bước chính (rút gọn)

```python
def build_packages(meta_path, pdf_root, out_dir, keep=True):
    rows = load_excel(meta_path)                  # đọc B→X, Y→AT
    groups = group_by_folder(pdf_root, rows)      # 1 thư mục = 1 hồ sơ

    for folder, items in groups.items():
        # 1) Trích arcFileCode từ tên file + đối chiếu
        arc = ensure_unique_arc_in_folder(items)  # cảnh báo nếu lệch STT/arc
        hoso = hydrate_hoso_from_rowset(items)    # B→X → HoSo(...)
        hoso.paper_file_code = hoso.arc_file_code # theo yêu cầu dự án

        # 2) Quét PDF
        for it in items:
            pdf = probe_pdf(it.path)              # size, mtime, sha256, pages
            hoso.tai_lieu.append(to_TaiLieu(it, pdf))

        # 3) Render EAD.xml, PREMIS.xml, rep1/METS.xml, METS gốc
        pkg_dir = create_pkg_tree(out_dir, folder)
        write_ead_xml(pkg_dir, hoso)
        write_premis_xml(pkg_dir, hoso)
        write_rep1(pkg_dir, hoso)                 # copies PDFs into rep1/data
        write_mets_root(pkg_dir, hoso)            # links EAD/PREMIS/rep1

        # 4) Nén
        zip_path = make_zip(pkg_dir)
        if not keep:
            remove_dir(pkg_dir)
```

---

# 12) Tài nguyên `schemas/` & template

* Đặt sẵn tối thiểu: `METS.xsd`, `EAD.xsd` (và biến thể `EAD_doc.xsd`), `PREMIS.xsd` trong `schemas/` và tham chiếu từ METS/PREMIS.&#x20;
* Template XML (Jinja2 hoặc lxml) phải **tự cập nhật `SIZE`/`CHECKSUM`** của chính file EAD/PREMIS vào `mdRef` tương ứng sau khi ghi ra đĩa.&#x20;

---

# 13) Kiểm thử chấp nhận (UAT) — danh sách ngắn

1. **Sinh 1 gói** từ 1 thư mục PDF có ≥2 tệp → zip + giữ thư mục (mặc định Y).
2. **Đường dẫn dài** (>260 ký tự Windows) → đọc/ghi/nén thành công.
3. **Sai STT** trong Excel so với tên tệp → log cảnh báo nhưng vẫn build; `structMap` vẫn đúng thứ tự.
4. **Thiếu PDF** so với hàng Excel → cảnh báo & bỏ qua dòng lỗi.
5. **Checksum**: thay 1 PDF rồi build lại → PREMIS/METS được cập nhật `SIZE/CHECKSUM`.&#x20;

---

# 14) Ghi chú tuân thủ TT 05/2025

Thiết kế này bảo đảm các **thuộc tính bắt buộc** của METS (`mdRef`, `FLocat`, `file`, `structMap`), **cấu trúc gói** (AIP\_hoso + rep1), **ràng buộc CSIP** (`csip:OAISPACKAGETYPE=AIP`), **liên kết EAD/PREMIS** theo Phụ lục I (chi tiết đã trích dẫn từ tài liệu đặc tả anh/chị cung cấp).&#x20;

---

Nếu anh/chị muốn, tôi có thể chuyển thiết kế này thành **bộ khung mã (scaffold)** với file `.py` đầy đủ, template XML, và bộ `schemas/` mẫu để chạy ngay trên dữ liệu thử.
