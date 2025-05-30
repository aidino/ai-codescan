# **AI CodeScan \- Danh sách Công việc Chi tiết (TASK.MD)**

Ngày tạo: 30 tháng 5, 2025  
Tên dự án: AI CodeScan  
Phiên bản: 1.0

## **Giai đoạn 0: Chuẩn bị và Thiết lập Nền tảng Dự án (Docker & Python)**

### **Task 0.1: Hoàn thiện tài liệu thiết kế chi tiết (DESIGN.MD)**

* [x] Rà soát và xác nhận lại tất cả các phần của DESIGN.MD.  
* [x] Bổ sung các chi tiết còn thiếu hoặc làm rõ các điểm chưa rõ ràng.

**Hoàn thành:** 
- ✅ Sửa lỗi mục lục và bookmark reference
- ✅ Bổ sung Phần V: Protocols và APIs Nội bộ Chi tiết
- ✅ Bổ sung Phần VI: Error Handling và Security Considerations  
- ✅ Bổ sung Phần VII: Deployment và Scaling Strategy
- ✅ Bổ sung Phần VIII: Testing Strategy và Quality Assurance
- ✅ Định nghĩa chi tiết các protocols: TDP, ASCP, LSRP, PDCS
- ✅ Chi tiết hóa CKG Query API Specification
- ✅ Hoàn thiện error handling strategy và security measures
- ✅ Đưa ra chiến lược deployment với Docker architecture  
- ✅ Định nghĩa testing strategy và quality gates

### **Task 0.2: Thiết lập môi trường phát triển cốt lõi**

* [x] Chọn và cài đặt phiên bản Python ổn định (ví dụ: Python 3.10+).  
* [x] Khởi tạo repository Git cho dự án.  
* [x] Kết nối repository Git với một remote (ví dụ: GitHub, GitLab).  
* [x] Quyết định và thiết lập công cụ quản lý dependencies (Poetry hoặc pip với requirements.txt).  
  * [x] Nếu dùng Poetry, khởi tạo pyproject.toml.  
  * [x] Nếu dùng pip, tạo file requirements.txt ban đầu.  
* [x] Tạo và kích hoạt môi trường ảo Python (ví dụ: venv, conda).

**Hoàn thành:**
- ✅ Sử dụng Python 3.12.9 (phiên bản mới hơn và ổn định hơn so với 3.11 đề xuất)
- ✅ Git repository đã được thiết lập và kết nối với remote origin
- ✅ Chọn Poetry làm dependency manager và tạo pyproject.toml hoàn chỉnh
- ✅ Cài đặt tất cả dependencies cần thiết bao gồm:
  - Streamlit cho Web UI
  - Neo4j driver cho graph database  
  - OpenAI client cho LLM integration
  - GitPython và PyGithub cho Git operations
  - Code analysis tools (flake8, pylint, black, mypy)
  - Testing framework (pytest với coverage)
  - Development tools (pre-commit, isort, sphinx)
- ✅ Môi trường virtual đã được kích hoạt và hoạt động tốt
- ✅ CLI application đã được tạo với các commands cơ bản
- ✅ Dockerfile và docker-compose.yml đã được thiết lập
- ✅ Neo4j container đã được test và hoạt động
- ✅ Scripts setup.sh và test_neo4j.py đã được tạo
- ✅ Cấu trúc thư mục theo architecture design đã được tạo

### **Task 0.3: Nghiên cứu và lựa chọn Agent Framework**

* \[ \] Nghiên cứu chi tiết về LangGraph: cách hoạt động, ưu/nhược điểm, ví dụ ứng dụng.  
* \[ \] (Tùy chọn) Nghiên cứu các agent framework mã nguồn mở khác phù hợp.  
* \[ \] Đưa ra quyết định về việc sử dụng LangGraph hoặc xây dựng cấu trúc agent tùy chỉnh.  
* \[ \] Ghi lại lý do lựa chọn.

### **Task 0.4: Xác định cấu trúc thư mục dự án chi tiết, thân thiện với Cursor AI**

* \[ \] Phác thảo cấu trúc thư mục chính (ví dụ: src/, tests/, docker/, docs/, scripts/).  
* \[ \] Thiết kế cấu trúc module con bên trong src/ cho từng TEAM Agent và các thành phần cốt lõi (ví dụ: src/agents/, src/core/).  
* \[ \] Đảm bảo quy ước đặt tên file và thư mục rõ ràng, nhất quán.

### **Task 0.5: Tạo Dockerfile cơ bản cho ứng dụng Python chính**

* \[ \] Chọn một base image Python phù hợp (ví dụ: python:3.10-slim).  
* \[ \] Thiết lập thư mục làm việc (WORKDIR) trong Dockerfile.  
* \[ \] Sao chép file quản lý dependencies (ví dụ: pyproject.toml và poetry.lock, hoặc requirements.txt) vào image.  
* \[ \] Cài đặt dependencies trong Dockerfile.  
* \[ \] Sao chép mã nguồn của ứng dụng vào image.  
* \[ \] Xác định ENTRYPOINT hoặc CMD để chạy ứng dụng (ban đầu có thể là một script placeholder).

### **Task 0.6: Thiết lập docker-compose.yml ban đầu**

* \[ \] Tạo file docker-compose.yml ở thư mục gốc dự án.  
* \[ \] Định nghĩa service cho ứng dụng Python chính:  
  * \[ \] Sử dụng Dockerfile đã tạo ở Task 0.5 (build context).  
  * \[ \] Cấu hình port mapping nếu ứng dụng có giao diện web sau này.  
  * \[ \] Cấu hình volume mapping cho source code để hỗ trợ live-reloading trong quá trình phát triển.  
* \[ \] Định nghĩa service cho Neo4j:  
  * \[ \] Sử dụng image Neo4j chính thức (ví dụ: neo4j:latest hoặc phiên bản cụ thể).  
  * \[ \] Cấu hình port mapping cho Neo4j (ví dụ: 7474, 7687).  
  * \[ \] Cấu hình volumes để lưu trữ dữ liệu Neo4j một cách bền vững.  
  * \[ \] Thiết lập biến môi trường cho Neo4j (ví dụ: NEO4J\_AUTH=neo4j/password).  
* \[ \] (Tùy chọn) Định nghĩa network chung cho các service.

### **Task 0.7: Cấu hình Neo4j Community Edition để chạy dưới dạng Docker container**

* \[ \] Xác nhận Neo4j service trong docker-compose.yml khởi động thành công.  
* \[ \] Kiểm tra khả năng truy cập Neo4j Browser qua port đã map.  
* \[ \] Kiểm tra khả năng kết nối tới Neo4j từ một script Python đơn giản (bên ngoài hoặc bên trong container ứng dụng nếu đã có).

## **Giai đoạn 1: Xây dựng Giao diện Web UI Cơ bản và Luồng Phân tích Python Đơn giản**

### **Task 1.1: Implement Orchestrator Agent (Cơ bản)**

* \[ \] Tạo thư mục src/core/orchestrator/.  
* \[ \] Tạo file orchestrator\_agent.py.  
* \[ \] Implement class OrchestratorAgent.  
* \[ \] Implement WorkflowEngineModule với logic điều phối tuần tự đơn giản (ví dụ: một danh sách các bước).  
* \[ \] Implement StateManagerModule để lưu trữ và cập nhật trạng thái tác vụ (ví dụ: sử dụng dictionary).  
* \[ \] Implement ErrorHandlingModule với try-catch cơ bản và logging.  
* \[ \] Định nghĩa cấu trúc dữ liệu (ví dụ: Pydantic models hoặc dataclasses) cho TaskDefinition và AgentStateCommunication.

### **Task 1.2: Implement TEAM Interaction & Tasking (Web UI \- Streamlit Cơ bản)**

* \[ \] Tạo thư mục src/agents/interaction\_tasking/.  
* \[ \] Tạo file web\_ui.py cho ứng dụng Streamlit.  
* \[ \] Thiết kế giao diện Streamlit cơ bản trong web\_ui.py:  
  * \[ \] st.title("AI CodeScan").  
  * \[ \] st.text\_input("GitHub Repository URL:") để người dùng nhập URL.  
  * \[ \] st.button("Phân tích Repository").  
  * \[ \] Khu vực st.text\_area("Kết quả phân tích:", height=300) hoặc st.code("", language="text") để hiển thị output.  
* \[ \] Implement class UserIntentParserAgent\_Web:  
  * \[ \] Hàm parse yêu cầu từ URL và action button trên Streamlit.  
* \[ \] Implement class DialogManagerAgent\_Web:  
  * \[ \] Quản lý trạng thái tương tác cơ bản (ví dụ: đang chờ input, đang xử lý, đã hiển thị kết quả).  
* \[ \] Implement class TaskInitiationAgent\_Web:  
  * \[ \] Hàm tạo đối tượng TaskDefinition từ URL repo đã nhập.  
* \[ \] Implement class PresentationAgent\_Web:  
  * \[ \] Hàm nhận dữ liệu kết quả (ví dụ: output từ linter) và cập nhật UI Streamlit.

### **Task 1.3: Implement TEAM Data Acquisition (Cơ bản cho Python Repo Công khai)**

* \[ \] Tạo thư mục src/agents/data\_acquisition/.  
* \[ \] Implement class GitOperationsAgent:  
  * \[ \] Hàm clone\_repository(repo\_url, local\_path) sử dụng thư viện gitpython (chỉ git clone \--depth 1).  
* \[ \] Implement class LanguageIdentifierAgent:  
  * \[ \] Hàm identify\_language(local\_path) để xác định là project Python (ví dụ: kiểm tra sự tồn tại của file .py, requirements.txt, pyproject.toml).  
* \[ \] Implement class DataPreparationAgent:  
  * \[ \] Hàm prepare\_project\_context(repo\_url, local\_path, language) để tạo đối tượng ProjectDataContext.

### **Task 1.4: Implement TEAM CKG Operations (Cơ bản cho Python)**

* \[ \] Tạo thư mục src/agents/ckg\_operations/.  
* \[ \] Implement class CodeParserCoordinatorAgent:  
  * \[ \] Hàm parse\_python\_project(project\_path) để duyệt qua các file .py và gọi Python AST parser.  
* \[ \] Implement class ASTtoCKGBuilderAgent:  
  * \[ \] Định nghĩa CKG Schema cơ bản cho Python (nodes: File, Function, Class; relationships: IMPORTS, CALLS, DEFINES\_FUNCTION, DEFINES\_CLASS) dưới dạng Python enums hoặc constants.  
  * \[ \] Hàm build\_ckg\_from\_ast(ast\_node, file\_path) để trích xuất thông tin và tạo Cypher queries.  
  * \[ \] Hàm save\_to\_neo4j(cypher\_queries) để thực thi queries lên Neo4j.  
* \[ \] Implement class CKGQueryInterfaceAgent:  
  * \[ \] Hàm get\_connection() để kết nối tới Neo4j (sử dụng driver neo4j).  
  * \[ \] Hàm ví dụ: get\_functions\_in\_file(file\_path) để truy vấn CKG.  
* \[ \] Viết script cấu hình Neo4j ban đầu (nếu cần, ví dụ: tạo constraints).

### **Task 1.5: Implement TEAM Code Analysis (Cơ bản cho Python)**

* \[ \] Tạo thư mục src/agents/code\_analysis/.  
* \[ \] Implement class StaticAnalysisIntegratorAgent:  
  * \[ \] Hàm run\_flake8(project\_path) để chạy Flake8 bằng subprocess và thu thập output.  
  * \[ \] Hàm parse\_flake8\_output(output\_str) để chuyển output text thành danh sách các "Finding" có cấu trúc.  
* \[ \] Implement class ContextualQueryAgent:  
  * \[ \] (Ban đầu có thể trống hoặc có các hàm placeholder).

### **Task 1.6: Implement TEAM LLM Services (Kết nối Cơ bản \- Chưa sử dụng nhiều)**

* \[ \] Tạo thư mục src/agents/llm\_services/.  
* \[ \] Implement class LLMProviderAbstractionLayer và OpenAIProvider:  
  * \[ \] Interface LLMProvider với hàm generate(prompt).  
  * \[ \] Class OpenAIProvider implement interface, gọi API OpenAI (cần API key).  
* \[ \] Implement class LLMGatewayAgent:  
  * \[ \] Hàm send\_test\_prompt() để gửi một prompt cố định đơn giản.

### **Task 1.7: Implement TEAM Synthesis & Reporting (Cơ bản cho Linter Output)**

* \[ \] Tạo thư mục src/agents/synthesis\_reporting/.  
* \[ \] Implement class FindingAggregatorAgent:  
  * \[ \] Hàm aggregate\_findings(list\_of\_findings) (ban đầu có thể chỉ là trả về danh sách).  
* \[ \] Implement class ReportGeneratorAgent:  
  * \[ \] Hàm generate\_linter\_report\_text(aggregated\_findings) để tạo một chuỗi báo cáo đơn giản.  
* \[ \] Implement class OutputFormatterAgent:  
  * \[ \] Hàm format\_for\_streamlit(report\_text) để chuẩn bị dữ liệu cho PresentationAgent\_Web.

### **Task 1.8: Tích hợp Luồng End-to-End Cơ bản (Qua Web UI, chạy với Docker)**

* \[ \] Trong web\_ui.py, khi người dùng click "Phân tích":  
  * \[ \] Gọi TaskInitiationAgent\_Web để tạo TaskDefinition.  
  * \[ \] Gửi TaskDefinition cho OrchestratorAgent.  
  * \[ \] OrchestratorAgent điều phối các TEAM:  
    * \[ \] DataAcquisition (clone, identify).  
    * \[ \] CKGOperations (parse, build CKG \- có thể log thông tin, chưa dùng CKG nhiều ở bước này).  
    * \[ \] CodeAnalysis (run Flake8).  
    * \[ \] SynthesisReporting (tạo report text).  
  * \[ \] OrchestratorAgent trả kết quả về cho PresentationAgent\_Web để hiển thị.  
* \[ \] Chạy toàn bộ hệ thống bằng docker-compose up \--build.  
* \[ \] Test luồng với một URL repo Python công khai.

### **Task 1.9: Tìm kiếm và chuẩn bị 1-2 project Python open-source đơn giản trên GitHub để làm dữ liệu test thực tế**

* \[ \] Xác định 2-3 project Python nhỏ (ví dụ: \< 50 file, \< 5000 dòng code) trên GitHub.  
* \[ \] Ghi lại URL của các project này để test.  
* \[ \] Thử chạy Flake8 thủ công trên các project này để có baseline.

### **Task 1.10: Viết Unit test và Integration test cơ bản**

* \[ \] Thiết lập framework test (ví dụ: pytest).  
* \[ \] Viết unit test cho các hàm logic chính trong các agent (ví dụ: parsing output Flake8, tạo Cypher query đơn giản).  
* \[ \] Viết một integration test cơ bản cho luồng phân tích Flake8 (có thể mock các lời gọi Git và Neo4j).

### **Task 1.11: Tài liệu hóa API nội bộ, quyết định thiết kế, và cấu hình Docker. Cập nhật docker-compose.yml và Dockerfile cho ứng dụng Streamlit**

* \[ \] Thêm docstrings cho các class và public methods.  
* \[ \] Cập nhật README.md với hướng dẫn cách chạy dự án bằng Docker Compose.  
* \[ \] Tinh chỉnh Dockerfile của ứng dụng Python để chạy Streamlit (ví dụ: CMD \["streamlit", "run", "src/agents/interaction\_tasking/web\_ui.py"\]).  
* \[ \] Đảm bảo port của Streamlit (mặc định 8501\) được map trong docker-compose.yml.

## **Giai đoạn 2: Mở rộng Hỗ trợ Ngôn ngữ và Tính năng Phân tích CKG Cơ bản trên Web UI**

### **Task 2.1: Mở rộng TEAM Data Acquisition cho PAT và Private Repo**

* \[ \] Implement logic trong PATHandlerAgent (nếu tách riêng) hoặc trong TEAM Interaction & Tasking để:  
  * \[ \] Hiển thị trường nhập PAT trên Web UI (Streamlit st.text\_input với type="password").  
  * \[ \] Lưu trữ PAT tạm thời một cách an toàn (ví dụ: trong session state của Streamlit, không ghi vào file).  
* \[ \] Cập nhật GitOperationsAgent để sử dụng PAT khi clone private repo.  
* \[ \] Cập nhật Web UI để ẩn/hiện trường nhập PAT khi cần.

### **Task 2.2: Mở rộng TEAM CKG Operations và TEAM Code Analysis cho Java**

* \[ \] Nghiên cứu cách tích hợp javaparser (Java) với Python:  
  * \[ \] Lựa chọn phương án (JEP, subprocess, Docker container riêng cho javaparser service).  
  * \[ \] Implement phương án đã chọn.  
* \[ \] Cập nhật CodeParserCoordinatorAgent để gọi parser Java.  
* \[ \] Mở rộng CKGSD cho các cấu trúc Java (Class, Method, Interface, Extends, Implements, Field, Call, Import).  
* \[ \] Cập nhật ASTtoCKGBuilderAgent để xử lý AST từ javaparser và tạo Cypher queries cho Java.  
* \[ \] Cập nhật CKGQueryInterfaceAgent với các hàm truy vấn đặc thù cho Java (nếu có).  
* \[ \] StaticAnalysisIntegratorAgent:  
  * \[ \] Tích hợp Checkstyle: chạy, parse output.  
  * \[ \] Tích hợp PMD: chạy, parse output.

### **Task 2.3: Mở rộng TEAM CKG Operations và TEAM Code Analysis cho Dart**

* \[ \] Nghiên cứu cách tích hợp analyzer package (Dart) với Python:  
  * \[ \] Lựa chọn và implement phương án tích hợp (subprocess, Docker container riêng).  
* \[ \] Cập nhật CodeParserCoordinatorAgent để gọi parser Dart.  
* \[ \] Mở rộng CKGSD cho các cấu trúc Dart (Class, Function, Method, Mixin, Extension, Import, Part).  
* \[ \] Cập nhật ASTtoCKGBuilderAgent để xử lý output từ Dart analyzer.  
* \[ \] Cập nhật CKGQueryInterfaceAgent cho Dart.  
* \[ \] StaticAnalysisIntegratorAgent: Tích hợp Dart Analyzer (linter rules).

### **Task 2.4: Mở rộng TEAM CKG Operations và TEAM Code Analysis cho Kotlin**

* \[ \] Nghiên cứu cách tích hợp Kotlin Compiler API hoặc Detekt (Kotlin) với Python:  
  * \[ \] Lựa chọn và implement phương án tích hợp.  
* \[ \] Cập nhật CodeParserCoordinatorAgent cho Kotlin.  
* \[ \] Mở rộng CKGSD cho các cấu trúc Kotlin (Class, Function, Property, Extension Function, Object, Data Class).  
* \[ \] Cập nhật ASTtoCKGBuilderAgent cho Kotlin.  
* \[ \] Cập nhật CKGQueryInterfaceAgent cho Kotlin.  
* \[ \] StaticAnalysisIntegratorAgent:  
  * \[ \] Tích hợp Detekt: chạy, parse output.  
  * \[ \] Tích hợp Ktlint: chạy, parse output.

### **Task 2.5: Implement Phân tích Kiến trúc Cơ bản trong ArchitecturalAnalyzerAgent**

* \[ \] Tạo thư mục/file cho ArchitecturalAnalyzerAgent trong src/agents/code\_analysis/.  
* \[ \] Implement hàm phát hiện circular dependencies:  
  * \[ \] Truy vấn CKG (thông qua CKGQueryInterfaceAgent) để lấy đồ thị phụ thuộc (ví dụ: giữa các file hoặc module dựa trên imports).  
  * \[ \] Sử dụng thuật toán phát hiện chu trình (ví dụ: DFS) trên đồ thị này.  
* \[ \] Implement hàm gợi ý public elements không sử dụng:  
  * \[ \] Truy vấn CKG để tìm các public classes/functions/methods.  
  * \[ \] Truy vấn CKG để kiểm tra xem chúng có được gọi từ bên ngoài module/file của chúng hay không (trong phạm vi codebase đã phân tích).  
  * \[ \] Thêm cảnh báo về hạn chế của phân tích tĩnh (reflection, DI).

### **Task 2.6: Cập nhật TEAM Synthesis & Reporting và Web UI**

* \[ \] FindingAggregatorAgent: Tổng hợp kết quả từ phân tích kiến trúc và linter cho các ngôn ngữ mới.  
* \[ \] ReportGeneratorAgent: Cập nhật logic để bao gồm các phát hiện kiến trúc trong báo cáo.  
* \[ \] Cập nhật Web UI (Streamlit):  
  * \[ \] Thêm lựa chọn ngôn ngữ project (hoặc logic tự động phát hiện nâng cao hơn trong LanguageIdentifierAgent).  
  * \[ \] Tạo mục riêng hoặc cách hiển thị rõ ràng cho các vấn đề kiến trúc (circular dependencies, unused public elements).  
  * \[ \] Hiển thị kết quả linter cho Java, Dart, Kotlin.

### **Task 2.7: Tìm kiếm và chuẩn bị các project open-source (Java, Dart, Kotlin) trên GitHub để test thực tế**

* \[ \] Tìm 1-2 project cho mỗi ngôn ngữ (Java, Dart, Kotlin) với kích thước và độ phức tạp vừa phải.  
* \[ \] Ghi lại URL và thử nghiệm thủ công (nếu có thể) để có baseline.

### **Task 2.8: Mở rộng Unit test và Integration test**

* \[ \] Viết unit test cho các parser/linter integration mới.  
* \[ \] Viết unit test cho logic phân tích kiến trúc.  
* \[ \] Mở rộng integration test để bao gồm các luồng phân tích cho Java, Dart, Kotlin.  
* \[ \] Nếu sử dụng Docker container riêng cho parser/linter, viết test cho việc giao tiếp với các container đó.

## **Giai đoạn 3: Tích hợp LLM Sâu hơn, Phân tích PR, Q\&A trên Web UI**

### **Task 3.1: Nâng cấp TEAM LLM Services**

* \[ \] Implement class PromptFormatterModule:  
  * \[ \] Tạo thư viện các prompt template (dưới dạng string templates hoặc file). Ví dụ:  
    * Prompt tóm tắt thay đổi trong PR.  
    * Prompt giải thích một đoạn code.  
    * Prompt trả lời câu hỏi về cấu trúc code.  
  * \[ \] Hàm format\_prompt(template\_name, context\_data) để điền dữ liệu vào template.  
* \[ \] Implement class ContextProviderModule:  
  * \[ \] Hàm prepare\_llm\_context(code\_snippets, ckg\_data, diffs, max\_tokens) để:  
    * Chọn lọc thông tin quan trọng.  
    * Cắt tỉa ngữ cảnh nếu quá dài (ví dụ: tóm tắt, chỉ lấy phần liên quan).  
    * Định dạng ngữ cảnh cho LLM (ví dụ: sử dụng Markdown, thẻ XML).  
* \[ \] Định nghĩa chi tiết LLMServiceRequest/Response Protocol (LSRP) (ví dụ: Pydantic models) bao gồm loại tác vụ, ngữ cảnh, tham số LLM, và cấu trúc kết quả.

### **Task 3.2: Nâng cấp TEAM Code Analysis cho LLM**

* \[ \] Implement đầy đủ class LLMAnalysisSupportAgent:  
  * \[ \] Hàm request\_code\_explanation(code\_snippet, related\_ckg\_info):  
    * Gọi ContextProviderModule để chuẩn bị ngữ cảnh.  
    * Gọi PromptFormatterModule để lấy prompt giải thích code.  
    * Tạo LLMServiceRequest và gửi tới LLMGatewayAgent.  
  * \[ \] Hàm request\_pr\_summary(diff\_text, affected\_components\_info):  
    * Chuẩn bị ngữ cảnh và prompt cho tóm tắt PR.  
    * Tạo và gửi LLMServiceRequest.  
  * \[ \] Hàm request\_qna\_answer(user\_question, code\_context, ckg\_context):  
    * Chuẩn bị ngữ cảnh và prompt cho Q\&A.  
    * Tạo và gửi LLMServiceRequest.

### **Task 3.3: Implement Phân tích Pull Request (PR) Cơ bản**

* \[ \] Cập nhật GitOperationsAgent:  
  * \[ \] Hàm get\_pr\_details(repo\_url, pr\_id, pat) để fetch thông tin PR (diff, metadata) từ API GitHub/GitLab (sử dụng thư viện như PyGithub).  
* \[ \] Cập nhật TEAM Code Analysis:  
  * \[ \] Logic phân tích diff (ví dụ: xác định file thay đổi, dòng thay đổi).  
  * \[ \] Sử dụng ContextualQueryAgent để truy vấn CKG, tìm các thành phần code (functions, classes) bị ảnh hưởng bởi thay đổi trong diff.  
  * \[ \] Gọi LLMAnalysisSupportAgent.request\_pr\_summary() để LLM tạo tóm tắt.  
* \[ \] Cập nhật TEAM Synthesis & Reporting:  
  * \[ \] Chuẩn bị dữ liệu tóm tắt PR để hiển thị.  
* \[ \] Cập nhật Web UI (Streamlit):  
  * \[ \] Thêm trường nhập PR ID (và chọn platform GitHub/GitLab).  
  * \[ \] Hiển thị tóm tắt PR (thay đổi chính, tác động tiềm ẩn cơ bản).

### **Task 3.4: Implement Hỏi-Đáp Tương tác (Q\&A Cơ bản)**

* \[ \] Cập nhật UserIntentParserAgent\_Web:  
  * \[ \] Nhận diện và trích xuất câu hỏi của người dùng từ một ô nhập liệu Q\&A trên Web UI.  
* \[ \] Cập nhật DialogManagerAgent\_Web:  
  * \[ \] Quản lý luồng hội thoại Q\&A (ví dụ: hiển thị câu hỏi, chờ câu trả lời).  
* \[ \] Cập nhật ContextualQueryAgent:  
  * \[ \] Hàm find\_code\_definition(entity\_name, entity\_type) để tìm định nghĩa class/function.  
  * \[ \] Hàm find\_callers\_or\_callees(function\_name, direction="callees").  
* \[ \] Tích hợp với LLMAnalysisSupportAgent.request\_qna\_answer():  
  * \[ \] Nếu CKG trả về kết quả trực tiếp, có thể dùng LLM để diễn giải tự nhiên hơn.  
  * \[ \] Nếu câu hỏi phức tạp hơn, cung cấp ngữ cảnh code/CKG cho LLM để trả lời.  
* \[ \] Cập nhật Web UI (Streamlit):  
  * \[ \] Thêm khu vực Q\&A: ô nhập câu hỏi, nút gửi, khu vực hiển thị câu trả lời.

### **Task 3.5: Cải thiện báo cáo trên Web UI với các giải thích/tóm tắt từ LLM**

* \[ \] ReportGeneratorAgent:  
  * \[ \] Khi có các phát hiện phức tạp (ví dụ: từ phân tích kiến trúc), có thể gọi LLM để sinh giải thích ngắn gọn, dễ hiểu.  
  * \[ \] Tích hợp các tóm tắt (PR, giải thích code) vào báo cáo tổng thể.  
* \[ \] Cập nhật Web UI để hiển thị các phần giải thích/tóm tắt này một cách trực quan.

### **Task 3.6: Mở rộng Unit test và Integration test**

* \[ \] Viết unit test cho PromptFormatterModule, ContextProviderModule.  
* \[ \] Viết unit test cho các hàm mới trong LLMAnalysisSupportAgent.  
* \[ \] Mock các lời gọi API LLM trong tests.  
* \[ \] Viết integration test cho luồng phân tích PR và Q\&A.

## **Giai đoạn 4: Sinh Sơ đồ trên Web UI và Cải tiến Trải nghiệm Người dùng**

### **Task 4.1: Implement Sinh Sơ đồ Lớp (Class Diagram Cơ bản) trong TEAM Synthesis & Reporting**

* \[ \] Implement class DiagramGeneratorAgent:  
  * \[ \] Hàm generate\_class\_diagram\_code(class\_name\_or\_module\_path, diagram\_type="plantuml"):  
    * Nhận yêu cầu từ Web UI.  
    * Gọi ContextualQueryAgent để truy vấn CKG lấy thông tin về class/module (thuộc tính, phương thức, quan hệ kế thừa, quan hệ với các class khác gần đó).  
    * Chuyển đổi thông tin này thành cú pháp PlantUML hoặc Mermaid.js.  
    * Trả về chuỗi mã nguồn sơ đồ.

### **Task 4.2: Cập nhật Web UI để hỗ trợ Sơ đồ**

* \[ \] Thêm chức năng trên Web UI (Streamlit) để người dùng:  
  * \[ \] Nhập tên class hoặc đường dẫn module muốn vẽ sơ đồ.  
  * \[ \] Chọn loại sơ đồ (ban đầu là Class Diagram).  
  * \[ \] Nút "Vẽ sơ đồ".  
* \[ \] Hiển thị sơ đồ:  
  * \[ \] Nếu dùng PlantUML: Nghiên cứu cách render PlantUML trong Streamlit (ví dụ: gọi PlantUML server, hoặc render thành ảnh rồi hiển thị st.image).  
  * \[ \] Nếu dùng Mermaid.js: Streamlit có component st\_mermaid hoặc có thể dùng st.markdown với cú pháp Mermaid.  
  * \[ \] Hoặc ban đầu chỉ hiển thị mã nguồn PlantUML/Mermaid để người dùng copy.

### **Task 4.3: Thu thập phản hồi người dùng và cải tiến UX/UI của Web App**

* \[ \] Tạo một form phản hồi đơn giản hoặc kênh thu thập ý kiến từ người dùng thử nghiệm.  
* \[ \] Dựa trên phản hồi, thực hiện các cải tiến:  
  * \[ \] Tối ưu hóa luồng nhập liệu và hiển thị kết quả.  
  * \[ \] Cải thiện bố cục, màu sắc, font chữ.  
  * \[ \] Thêm các hướng dẫn, tooltip nếu cần.

### **Task 4.4: Nghiên cứu và tích hợp các thư viện Streamlit component tùy chỉnh nếu cần**

* \[ \] Tìm kiếm các Streamlit component trên awesome-streamlit.org hoặc các nguồn khác có thể cải thiện:  
  * \[ \] Hiển thị bảng dữ liệu tương tác.  
  * \[ \] Trực quan hóa đồ thị (ngoài Mermaid/PlantUML).  
  * \[ \] Các thành phần UI phức tạp hơn.  
* \[ \] Thử nghiệm và tích hợp các component phù hợp.

## **Giai đoạn 5 trở đi: Nghiên cứu Chuyên sâu và Cải tiến Liên tục (Các Chủ đề Nghiên cứu)**

(Đối với Giai đoạn 5, các task sẽ mang tính nghiên cứu, thử nghiệm (PoC), đánh giá, và sau đó là tích hợp nếu thành công. Dưới đây là ví dụ cho một vài chủ đề)

### **Phase 5.1 (Nghiên cứu Orchestrator)**

* **Chủ đề: Adaptive and Dynamic Workflow Orchestration**  
  * \[ \] Nghiên cứu các kỹ thuật điều phối luồng công việc động.  
  * \[ \] Thiết kế thử nghiệm cách Orchestrator có thể thay đổi luồng dựa trên loại project hoặc kết quả phân tích ban đầu.  
  * \[ \] Implement PoC.  
  * \[ \] Đánh giá và quyết định tích hợp.  
* **Chủ đề: Advanced Fault Tolerance and Recovery Strategies**  
  * \[ \] Nghiên cứu các chiến lược xử lý lỗi nâng cao (ví dụ: retry có backoff, circuit breaker, bù trừ tác vụ).  
  * \[ \] Thiết kế và implement PoC cho Orchestrator.  
  * \[ \] Đánh giá và tích hợp.

### **Phase 5.4 (Nghiên cứu TEAM CKG Operations)**

* **Chủ đề: Xây dựng CKG Tăng tiến (Incremental CKG Updates)**  
  * \[ \] Nghiên cứu thuật toán cập nhật CKG dựa trên diff mã nguồn.  
  * \[ \] Thiết kế cách lưu trữ phiên bản hoặc phát hiện thay đổi hiệu quả.  
  * \[ \] Implement PoC cho việc cập nhật CKG khi có commit mới hoặc PR.  
  * \[ \] Đánh giá hiệu năng và độ chính xác.

### **Phase 5.6 (Nghiên cứu TEAM LLM Services)**

* **Chủ đề: Advanced Retrieval Augmented Generation (RAG) for Code Understanding**  
  * \[ \] Nghiên cứu các kiến trúc RAG tiên tiến sử dụng CKG làm knowledge base.  
  * \[ \] Thiết kế hệ thống RAG để truy xuất code snippets và thông tin CKG liên quan đến câu hỏi/tác vụ.  
  * \[ \] Implement PoC cho Q\&A hoặc giải thích code dựa trên RAG.  
  * \[ \] Đánh giá chất lượng câu trả lời/giải thích.

(Lặp lại quy trình Nghiên cứu \-\> Thiết kế PoC \-\> Implement PoC \-\> Đánh giá \-\> Tích hợp cho các chủ đề nghiên cứu khác đã liệt kê trong PLAN.MD)

## **Quản lý Dự án và Rủi ro (Không phải task cụ thể, mà là các hoạt động liên tục)**

* \[ \] Tổ chức họp sprint planning và review định kỳ.  
* \[ \] Cập nhật tiến độ trên công cụ theo dõi (ví dụ: GitHub Issues).  
* \[ \] Thực hiện code review cho tất cả các thay đổi.  
* \[ \] Theo dõi và giải quyết các rủi ro đã xác định trong PLAN.MD.