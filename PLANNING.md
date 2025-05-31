# **AI CodeScan \- Kế hoạch Triển khai Dự án v1.0**

Ngày tạo: 30 tháng 5, 2025  
Tên dự án: AI CodeScan  
Phiên bản: 1.0

## **Mục tiêu Kế hoạch**

Kế hoạch này phác thảo các giai đoạn và nhiệm vụ chính để triển khai phiên bản 1.0 của dự án AI CodeScan, với ưu tiên phát triển giao diện người dùng Web (Web UI) từ sớm và tận dụng Cursor AI làm IDE chính. Các giai đoạn đầu tập trung vào việc xây dựng nền tảng, giao diện Web UI cơ bản và các tính năng cốt lõi. Các giai đoạn sau sẽ mở rộng chức năng và thực hiện các nghiên cứu chuyên sâu.

**Lưu ý về IDE và Context cho AI:**

* Dự án sẽ sử dụng **Cursor AI** làm IDE chính.  
* Cấu trúc dự án, code và comment sẽ được tổ chức một cách rõ ràng, mạch lạc để tối ưu hóa khả năng hiểu context của Cursor AI và các công cụ AI hỗ trợ phát triển khác.

## **Giai đoạn 0: Chuẩn bị và Thiết lập Nền tảng Dự án (Docker & Python)**

* **Task 0.1:** Hoàn thiện tài liệu thiết kế chi tiết (DESIGN.MD).  
* **Task 0.2:** Thiết lập môi trường phát triển cốt lõi:  
  * Chọn ngôn ngữ lập trình chính (Python).  
  * Thiết lập hệ thống quản lý phiên bản (Git, GitHub/GitLab).  
  * Thiết lập công cụ quản lý dependencies (ví dụ: Poetry hoặc pip với requirements.txt).  
  * Thiết lập môi trường ảo Python.  
* **Task 0.3:** Nghiên cứu và lựa chọn Agent Framework (ví dụ: LangGraph cho Orchestrator, hoặc xây dựng cấu trúc agent tùy chỉnh).  
* **Task 0.4:** Xác định cấu trúc thư mục dự án chi tiết, thân thiện với Cursor AI.  
* **Task 0.5:** **Tạo Dockerfile cơ bản cho ứng dụng Python chính.**  
* **Task 0.6:** **Thiết lập docker-compose.yml ban đầu để quản lý các service (ví dụ: ứng dụng Python, Neo4j).**  
* **Task 0.7:** Cấu hình Neo4j Community Edition để chạy dưới dạng Docker container thông qua docker-compose.yml.

## **Giai đoạn 1: Xây dựng Giao diện Web UI Cơ bản và Luồng Phân tích Python Đơn giản**

* **Mục tiêu:** Tạo ra một phiên bản MVP với giao diện Web UI (Streamlit) cơ bản, có khả năng thực hiện và hiển thị kết quả phân tích linter (Flake8) cho một repository Python công khai, chạy trong môi trường Docker.  
* **Task 1.1: Implement Orchestrator Agent (Cơ bản)**  
  * WorkflowEngineModule: Điều phối luồng tác vụ tuần tự đơn giản.  
  * StateManagerModule: Theo dõi trạng thái tác vụ cơ bản.  
  * ErrorHandlingModule: Xử lý lỗi cơ bản.  
  * Định nghĩa Task Definition Protocol (TDP) và Agent State Communication Protocol (ASCP) sơ bộ.  
* **Task 1.2: Implement TEAM Interaction & Tasking (Web UI \- Streamlit Cơ bản)**  
  * Thiết kế và triển khai giao diện Web UI Streamlit cơ bản:  
    * Input URL repository.  
    * Nút "Phân tích".  
    * Khu vực hiển thị output dạng text đơn giản (kết quả linter).  
  * UserIntentParserAgent: Phân tích ý định cơ bản từ Web UI (ví dụ: yêu cầu review repo từ URL).  
  * DialogManagerAgent: Quản lý tương tác cơ bản trên Web UI.  
  * TaskInitiationAgent: Tạo TaskDefinition từ input Web UI.  
  * PresentationAgent: Định dạng và gửi dữ liệu để hiển thị trên Streamlit.  
* **Task 1.3: Implement TEAM Data Acquisition (Cơ bản cho Python Repo Công khai)**  
  * GitOperationsAgent: Clone public repo Python (git clone \--depth 1).  
  * LanguageIdentifierAgent: Xác định ngôn ngữ Python.  
  * DataPreparationAgent: Tạo ProjectDataContext cơ bản.  
  * (Tạm thời bỏ qua PATHandlerAgent cho public repo).  
* **Task 1.4: Implement TEAM CKG Operations (Cơ bản cho Python)**  
  * CodeParserCoordinatorAgent: Điều phối parser Python (sử dụng module ast).  
  * ASTtoCKGBuilderAgent: Xây dựng CKG cơ bản cho Python (nodes: file, function, class; relationships: calls, imports) vào Neo4j.  
  * Định nghĩa CKG Schema Definition (CKGSD) cơ bản cho Python.  
  * CKGQueryInterfaceAgent: Cung cấp API truy vấn CKG cơ bản.  
* **Task 1.5: Implement TEAM Code Analysis (Cơ bản cho Python)**  
  * StaticAnalysisIntegratorAgent: Tích hợp Flake8 cho Python. Chạy linter, thu thập và chuẩn hóa output.  
  * ContextualQueryAgent: Truy vấn CKG lấy thông tin cơ bản nếu cần cho việc chuẩn bị chạy linter.  
* **Task 1.6: Implement TEAM LLM Services (Kết nối Cơ bản \- Chưa sử dụng nhiều)**  
  * LLMProviderAbstractionLayer: Interface và implementation cơ bản cho OpenAI API.  
  * LLMGatewayAgent: Khả năng gửi một prompt thử nghiệm.  
* **Task 1.7: Implement TEAM Synthesis & Reporting (Cơ bản cho Linter Output)**  
  * FindingAggregatorAgent: Tổng hợp kết quả từ Flake8.  
  * ReportGeneratorAgent: Tạo báo cáo text đơn giản từ kết quả Flake8.  
  * OutputFormatterAgent: Chuẩn bị output cho PresentationAgent (Streamlit).  
* **Task 1.8: Tích hợp Luồng End-to-End Cơ bản (Qua Web UI, chạy với Docker)**  
  * Người dùng nhập URL repo Python qua Web UI.  
  * Hệ thống clone, parse, xây dựng CKG (kết nối Neo4j container), chạy Flake8.  
  * Hiển thị kết quả Flake8 trên Web UI.  
* **Task 1.9: Tìm kiếm và chuẩn bị 1-2 project Python open-source đơn giản trên GitHub để làm dữ liệu test thực tế.**  
* **Task 1.10:** Viết Unit test và Integration test cơ bản.  
* **Task 1.11:** Tài liệu hóa API nội bộ, quyết định thiết kế, và cấu hình Docker. Cập nhật docker-compose.yml và Dockerfile cho ứng dụng Streamlit.

## **Giai đoạn 2: Mở rộng Hỗ trợ Ngôn ngữ và Tính năng Phân tích CKG Cơ bản trên Web UI**

* **Mục tiêu:** Hỗ trợ thêm Java, Dart, Kotlin. Implement và hiển thị các tính năng phân tích kiến trúc cơ bản từ CKG (circular dependencies, unused public elements) trên Web UI.  
* **Task 2.1: Mở rộng TEAM Data Acquisition cho PAT và Private Repo**  
  * Implement PATHandlerAgent: Yêu cầu PAT từ người dùng qua Web UI, lưu trữ tạm thời và an toàn.  
  * Cập nhật GitOperationsAgent để sử dụng PAT.  
  * Cập nhật Web UI để cho phép nhập PAT.  
* **Task 2.2: Mở rộng TEAM CKG Operations và TEAM Code Analysis cho Java**  
  * Tích hợp javaparser (cân nhắc chạy javaparser trong Docker container riêng nếu quản lý dependencies phức tạp).  
  * Cập nhật CodeParserCoordinatorAgent, CKGSD, ASTtoCKGBuilderAgent, CKGQueryInterfaceAgent cho Java.  
  * StaticAnalysisIntegratorAgent: Tích hợp Checkstyle/PMD cho Java.  
* **Task 2.3: Mở rộng TEAM CKG Operations và TEAM Code Analysis cho Dart**  
  * Tích hợp analyzer package của Dart (cân nhắc chạy trong Docker container riêng).  
  * Cập nhật các agent và schema liên quan cho Dart.  
  * StaticAnalysisIntegratorAgent: Tích hợp Dart Analyzer.  
* **Task 2.4: Mở rộng TEAM CKG Operations và TEAM Code Analysis cho Kotlin**  
  * Tích hợp Kotlin Compiler API hoặc Detekt (cân nhắc chạy trong Docker container riêng).  
  * Cập nhật các agent và schema liên quan cho Kotlin.  
  * StaticAnalysisIntegratorAgent: Tích hợp Detekt/Ktlint cho Kotlin.  
* **Task 2.5: Implement Phân tích Kiến trúc Cơ bản trong ArchitecturalAnalyzerAgent**  
  * Phát hiện circular dependencies (file/module level) dựa trên CKG.  
  * Gợi ý public elements không sử dụng (với cảnh báo).  
* **Task 2.6: Cập nhật TEAM Synthesis & Reporting và Web UI**  
  * Tổng hợp kết quả phân tích kiến trúc và linter cho các ngôn ngữ mới vào báo cáo.  
  * Cập nhật Web UI để:  
    * Cho phép chọn/tự động phát hiện ngôn ngữ của project.  
    * Hiển thị kết quả phân tích kiến trúc.  
    * Hiển thị kết quả linter cho các ngôn ngữ mới.  
* **Task 2.7: Tìm kiếm và chuẩn bị các project open-source (Java, Dart, Kotlin) trên GitHub để test thực tế.**  
* **Task 2.8:** Mở rộng Unit test và Integration test, bao gồm test tương tác giữa container.

## **Giai đoạn 3: Tích hợp LLM Sâu hơn, Phân tích PR, Q\&A trên Web UI**

* **Mục tiêu:** Tăng cường vai trò của LLM. Implement và hiển thị phân tích PR cơ bản, Q\&A cơ bản, và giải thích code từ LLM trên Web UI.  
* **Task 3.1: Nâng cấp TEAM LLM Services**  
  * Implement PromptFormatterModule: Thư viện prompt template cho các tác vụ (tóm tắt PR, giải thích code, trả lời Q\&A).  
  * Implement ContextProviderModule: Xử lý ngữ cảnh (code snippets, CKG data, diffs) cho LLM.  
  * Xây dựng LLMServiceRequest/Response Protocol (LSRP) chi tiết.  
* **Task 3.2: Nâng cấp TEAM Code Analysis cho LLM**  
  * Implement LLMAnalysisSupportAgent đầy đủ: Chuẩn bị ngữ cảnh, tạo LLMServiceRequest cho các tác vụ.  
* **Task 3.3: Implement Phân tích Pull Request (PR) Cơ bản**  
  * GitOperationsAgent: Fetch thông tin PR (diffs, metadata).  
  * TEAM Code Analysis:  
    * Phân tích diff của PR.  
    * Sử dụng CKG để xác định các thành phần bị ảnh hưởng.  
    * Sử dụng TEAM LLM Services để tạo tóm tắt thay đổi và tác động "mức độ 1".  
  * TEAM Synthesis & Reporting: Chuẩn bị tóm tắt PR cho Web UI.  
  * Cập nhật Web UI để nhập thông tin PR và hiển thị tóm tắt.  
* **Task 3.4: Implement Hỏi-Đáp Tương tác (Q\&A Cơ bản)**  
  * UserIntentParserAgent: Nhận diện câu hỏi về cấu trúc code từ Web UI.  
  * DialogManagerAgent: Xử lý luồng Q\&A trên Web UI.  
  * ContextualQueryAgent: Truy vấn CKG để tìm thông tin.  
  * Sử dụng TEAM LLM Services để diễn giải kết quả CKG hoặc trả lời trực tiếp các câu hỏi dựa trên ngữ cảnh code.  
  * Cập nhật Web UI cho phép người dùng đặt câu hỏi và hiển thị câu trả lời.  
* **Task 3.5: Cải thiện báo cáo trên Web UI với các giải thích/tóm tắt từ LLM.**  
* **Task 3.6:** Mở rộng Unit test và Integration test.

## **Giai đoạn 4: Sinh Sơ đồ trên Web UI và Cải tiến Trải nghiệm Người dùng**

* **Mục tiêu:** Implement tính năng sinh class diagram và hiển thị trên Web UI. Liên tục cải thiện trải nghiệm người dùng.  
* **Task 4.1: Implement Sinh Sơ đồ Lớp (Class Diagram Cơ bản) trong TEAM Synthesis & Reporting**  
  * DiagramGeneratorAgent:  
    * Nhận yêu cầu sinh sơ đồ cho class/module cụ thể từ Web UI.  
    * Truy vấn CKG để lấy thông tin.  
    * Sinh mã PlantUML hoặc Mermaid.js.  
* **Task 4.2: Cập nhật Web UI để hỗ trợ Sơ đồ**  
  * Cho phép người dùng yêu cầu sinh sơ đồ cho một class/module.  
  * Hiển thị sơ đồ (render PlantUML/Mermaid.js trực tiếp trong Streamlit nếu có thể, hoặc hiển thị dưới dạng ảnh/mã).  
* **Task 4.3: Thu thập phản hồi người dùng và cải tiến UX/UI của Web App.**  
  * Tối ưu hóa luồng làm việc trên Web UI.  
  * Cải thiện cách trình bày thông tin.  
* **Task 4.4:** Nghiên cứu và tích hợp các thư viện Streamlit component tùy chỉnh nếu cần để nâng cao trải nghiệm.

## **Giai đoạn 5 trở đi: Nghiên cứu Chuyên sâu và Cải tiến Liên tục (Các Chủ đề Nghiên cứu)**

* **Mục tiêu:** Thực hiện các nghiên cứu chuyên sâu đã được đề xuất trong tài liệu thiết kế để cải thiện và mở rộng khả năng của AI CodeScan. Mỗi chủ đề nghiên cứu lớn có thể là một Phase riêng hoặc một tập hợp các Task trong một Phase lớn hơn.  
* **Ví dụ các Phase/Nhóm Task:**  
  * **Phase 5.1 (Nghiên cứu Orchestrator):**  
    * Task: Nghiên cứu và thử nghiệm Adaptive and Dynamic Workflow Orchestration.  
    * Task: Nghiên cứu và thử nghiệm Advanced Fault Tolerance and Recovery Strategies.  
    * Task: Nghiên cứu Resource Management for Concurrent Tasks.  
  * **Phase 5.2 (Nghiên cứu TEAM Interaction & Tasking \- Web UI Focus):**  
    * Task: Nghiên cứu Advanced NLU for Developer Queries (qua Web UI).  
    * Task: Nghiên cứu Proactive and Context-Aware Dialog Management (trên Web UI).  
  * **Phase 5.3 (Nghiên cứu TEAM Data Acquisition):**  
    * Task: Nghiên cứu Advanced Language & Framework Detection.  
    * Task: Nghiên cứu Efficient Handling of Very Large Repositories.  
  * **Phase 5.4 (Nghiên cứu TEAM CKG Operations):**  
    * Task: Nghiên cứu Tối ưu Schema CKG cho Phân tích Đa Ngôn ngữ và Sâu.  
    * Task: Phát triển Xây dựng CKG Tăng tiến (Incremental CKG Updates).  
    * Task: Nghiên cứu Kỹ thuật Semantic Enrichment cho CKG.  
  * **Phase 5.5 (Nghiên cứu TEAM Code Analysis):**  
    * Task: Phát triển Phát hiện Anti-Pattern Kiến trúc Nâng cao.  
    * Task: Nghiên cứu Phân tích Luồng Dữ liệu (Data Flow Analysis) trên CKG.  
    * Task: Nghiên cứu Đánh giá Rủi ro Thay đổi và Phân tích Tác động PR Sâu sắc.  
  * **Phase 5.6 (Nghiên cứu TEAM LLM Services):**  
    * Task: Thiết kế Tối ưu và Linh hoạt cho LLM Abstraction Layer.  
    * Task: Phát triển Advanced Retrieval Augmented Generation (RAG) for Code Understanding.  
    * Task: Xây dựng Robust Prompt Engineering Framework.  
  * **Phase 5.7 (Nghiên cứu TEAM Synthesis & Reporting \- Web UI Focus):**  
    * Task: Nghiên cứu Tự động Tạo Báo cáo Review Code Thông minh (hiển thị tối ưu trên Web).  
    * Task: Nghiên cứu Trực quan hóa Dữ liệu Phân tích Code Nâng cao và Tương tác (trên Web UI).  
* **Quy trình chung cho mỗi Chủ đề Nghiên cứu:**  
  1. Nghiên cứu lý thuyết và các giải pháp hiện có.  
  2. Đề xuất giải pháp/thiết kế thử nghiệm.  
  3. Implement prototype.  
  4. Đánh giá kết quả.  
  5. Tích hợp vào hệ thống chính nếu thành công.

## **Quản lý Dự án và Rủi ro**

* **Quản lý:**  
  * Họp sprint planning và review đều đặn (ví dụ: 2 tuần/sprint).  
  * Theo dõi tiến độ (có thể dùng GitHub Issues/Projects hoặc công cụ đơn giản khác).  
  * Review code thường xuyên.  
* **Rủi ro tiềm ẩn và Giải pháp sơ bộ:**  
  * **Khó khăn trong việc tích hợp các parser/tools ngoại vi:** Dành thời gian nghiên cứu kỹ, ưu tiên giải pháp chạy trong container riêng (sử dụng Docker) để cô lập dependencies.  
  * **Hiệu năng CKG với codebase lớn:** Tối ưu schema và truy vấn Neo4j, xem xét CKG tăng tiến sớm.  
  * **Chất lượng output từ LLM:** Đầu tư vào prompt engineering, RAG, và chiến lược đánh giá/giảm thiểu ảo giác.  
  * **Giới hạn API của LLM (rate limits, chi phí):** Thiết kế cơ chế retry, caching, và theo dõi chi phí.  
  * **Phạm vi dự án mở rộng quá nhanh:** Tập trung vào các mục tiêu của từng giai đoạn, quản lý backlog chặt chẽ.  
  * **Phức tạp trong quản lý và debug môi trường Dockerized:** Đảm bảo logging đầy đủ, sử dụng các công cụ debug Docker, và xây dựng kiến thức về Docker trong team.  
  * **Thách thức trong việc phát triển Web UI (Streamlit) đáp ứng đủ các tính năng phức tạp:** Nghiên cứu kỹ khả năng của Streamlit, xem xét các component tùy chỉnh, hoặc đánh giá lại framework UI nếu cần cho các tính năng rất nâng cao.

Kế hoạch này sẽ được cập nhật và điều chỉnh dựa trên tiến độ thực tế và các phát hiện trong quá trình phát triển.