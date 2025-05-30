# **AI CodeScan \- Báo cáo Thiết kế Toàn diện v1.0**

Ngày tạo: 30 tháng 5, 2025  
Tên dự án: AI CodeScan  
Phiên bản: 1.0

## **Mục lục**

1. Phần I: Giới thiệu, Tầm nhìn và Mục tiêu Dự án  
   1.1. Bối cảnh và Vấn đề Hiện tại  
   1.2. Tầm nhìn Giải pháp: AI CodeScan  
   1.3. Mục tiêu Tổng thể của AI CodeScan (Dài hạn)  
   1.4. Mục tiêu và Phạm vi cụ thể cho AI CodeScan v1.0 (Yêu cầu Bắt buộc)  
   1.5. Mục đích của Tài liệu này  
2. Phần II: Kiến trúc Hệ thống Tổng quan của AI CodeScan  
   2.1. Sơ đồ Tương tác Tổng quan giữa các TEAM Agent  
   2.2. Các TEAM Agent chính  
3. Phần III: Thiết kế Chi tiết các TEAM Agent  
   3.1. A. Orchestrator Agent (Agent Điều phối Trung tâm)  
   3.2. B. TEAM Interaction & Tasking (Đội Tương tác & Quản lý Tác vụ)  
   3.3. C. TEAM Data Acquisition (Đội Thu thập & Chuẩn bị Dữ liệu)  
   3.4. D. TEAM CKG Operations (Đội Vận hành Code Knowledge Graph)  
   3.5. E. TEAM Code Analysis (Đội Phân tích Mã nguồn)  
   3.6. F. TEAM LLM Services (Đội Dịch vụ LLM)  
   3.7. G. TEAM Synthesis & Reporting (Đội Tổng hợp & Báo cáo)  
4. [Phần IV: Công nghệ và Công cụ Đề xuất cho v1.0](#bookmark=id.ypdlsqmn5jhd)

## **Phần I: Giới thiệu, Tầm nhìn và Mục tiêu Dự án**

### **1.1. Bối cảnh và Vấn đề Hiện tại**

Trong bối cảnh phát triển phần mềm hiện đại, quy trình review code đóng một vai trò then chốt trong việc đảm bảo chất lượng, phát hiện lỗi sớm và chia sẻ kiến thức trong đội ngũ. Tuy nhiên, quy trình này thường tốn nhiều thời gian và công sức của các nhà phát triển cấp cao, dễ bị ảnh hưởng bởi yếu tố con người, và có thể bỏ sót các vấn đề phức tạp liên quan đến kiến trúc hệ thống hoặc các tác động tiềm ẩn của thay đổi mã nguồn. Các công cụ review code tự động hiện tại phần lớn tập trung vào việc kiểm tra cú pháp, tuân thủ quy tắc định dạng (linting), hoặc phát hiện các lỗi bề mặt, chứ chưa thực sự "hiểu" được logic, ngữ nghĩa và kiến trúc tổng thể của codebase.

### **1.2. Tầm nhìn Giải pháp: AI CodeScan**

**AI CodeScan** được hình dung như một trợ lý review code AI thông minh, một "đồng đội ảo" thế hệ mới cho các nhà phát triển. Mục tiêu là vượt qua những hạn chế của các công cụ truyền thống bằng cách cung cấp khả năng phân tích sâu sắc, hiểu biết ngữ cảnh và tương tác linh hoạt. AI CodeScan sẽ không chỉ là một công cụ phát hiện lỗi, mà còn là một cố vấn kiến trúc, một người hướng dẫn và một nền tảng chia sẻ tri thức về codebase.

### **1.3. Mục tiêu Tổng thể của AI CodeScan (Dài hạn)**

* Cung cấp các phân tích kiến trúc sâu sắc, tự động xác định các anti-pattern, đánh giá sự tuân thủ các nguyên tắc thiết kế.  
* Đưa ra những đánh giá tác động của Pull Request (PR) một cách toàn diện, bao gồm cả các ảnh hưởng tiềm ẩn đến các module khác hoặc các khía cạnh phi chức năng.  
* Cho phép tương tác hỏi-đáp (Q\&A) một cách tự nhiên về codebase, giúp nhà phát triển nhanh chóng hiểu rõ các phần code phức tạp hoặc tìm kiếm thông tin liên quan.  
* Hỗ trợ đa dạng ngôn ngữ lập trình phổ biến.  
* Cung cấp giao diện người dùng thân thiện, trực quan và mang tính hội thoại.  
* Liên tục học hỏi và cải thiện từ phản hồi của người dùng và các codebase mới.

### **1.4. Mục tiêu và Phạm vi cụ thể cho AI CodeScan v1.0 (Yêu cầu Bắt buộc)**

Phiên bản 1.0 của AI CodeScan sẽ tập trung vào việc xây dựng nền tảng cốt lõi và cung cấp các tính năng thiết yếu để chứng minh giá trị của giải pháp.

* **Ngôn ngữ Lập trình Bắt buộc Hỗ trợ:**  
  * Android: Java, Kotlin  
  * Flutter: Dart  
  * Python  
* **Các Tính năng Cốt lõi của v1.0:**  
  1. **Xây dựng Code Knowledge Graph (CKG):** Tạo CKG cơ bản cho các ngôn ngữ mục tiêu, nắm bắt các cấu trúc (files, classes, functions/methods, interfaces) và mối quan hệ chính (lời gọi hàm/method trực tiếp, kế thừa, hiện thực hóa, import/dependencies).  
  2. **Phân tích Kiến trúc (Cơ bản):**  
     * Phát hiện circular dependencies ở cấp độ file/module.  
     * Gợi ý các public elements (methods, classes) có khả năng không được sử dụng trong phạm vi codebase đã phân tích (cần có cảnh báo rõ ràng về hạn chế của phân tích tĩnh trong trường hợp này, ví dụ như reflection, DI).  
  3. **Phân tích Pull Request (PR) (Cơ bản):**  
     * Phân tích diff của PR.  
     * Cung cấp tóm tắt bằng văn bản về các thay đổi chính và các tác động trực tiếp ở "mức độ 1" (ví dụ: function A được thay đổi, function A được gọi bởi B và gọi đến C).  
  4. **Hỏi-Đáp Tương tác (Q\&A Cơ bản):** Cho phép người dùng đặt các câu hỏi đơn giản về cấu trúc code (ví dụ: "Định nghĩa của class X ở đâu?", "Function Y gọi những hàm nào trong file này?").  
  5. **Sinh** Sơ **đồ Lớp (Class Diagram Cơ bản):** Tạo class diagram đơn giản theo yêu cầu cho một class hoặc module cụ thể.  
  6. **Giao diện Tương tác:** Ban đầu thông qua giao diện dòng lệnh (CLI) hoặc một giao diện web đơn giản (ví dụ: sử dụng Streamlit).  
* **Chiến lược LLM cho v1.0:**  
  * Sử dụng API của OpenAI (ví dụ: các model GPT) làm LLM chính cho các tác vụ xử lý ngôn ngữ tự nhiên, tóm tắt và hỗ trợ Q\&A.  
  * Thiết kế hệ thống phải đảm bảo **khả năng mở rộng và thay thế** dễ dàng sang các nhà cung cấp LLM khác hoặc các mô hình LLM chạy local trong tương lai.  
* **Xử lý Personal Access Token (PAT):**  
  * PAT **sẽ không được lưu trữ** một cách bền vững.  
  * Khi cần thiết cho các thao tác với Git (ví dụ: clone private repo), chatbot sẽ yêu cầu người dùng cung cấp PAT.  
  * PAT chỉ được sử dụng trong session hiện tại và sẽ được xóa khỏi bộ nhớ hoạt động (và ẩn khỏi lịch sử chat nếu có thể) ngay sau khi hoàn thành tác vụ.  
* **Xử lý Repository:**  
  * Khi clone repository, chỉ lấy code ở HEAD (git clone \--depth 1 ...) để tối ưu thời gian và tài nguyên.  
* **Ưu tiên Công nghệ:** Ưu tiên sử dụng các thư viện và công cụ mã nguồn mở cho tất cả các thành phần không phải là LLM API (ví dụ: CKG, parsers, tools, agent framework). Ngôn ngữ phát triển chính cho các agent dự kiến là Python.

### **1.5. Mục đích của Tài liệu này**

Tài liệu này trình bày thiết kế chi tiết cho phiên bản 1.0 của AI CodeScan. Đồng thời, nó cũng đóng vai trò là một bản yêu cầu nghiên cứu chuyên sâu, đặt ra các câu hỏi và lĩnh vực cần sự phân tích từ Gemini Deep Research để tối ưu hóa, xác thực và nâng cao thiết kế hiện tại, cũng như định hướng cho các phiên bản tương lai.

## **Phần II: Kiến trúc Hệ thống Tổng quan của AI CodeScan**

AI CodeScan được thiết kế dựa trên kiến trúc đa agent (Agentic Multi-Agent System). Hệ thống bao gồm một tập hợp các "TEAM" agent chuyên biệt, mỗi TEAM chịu trách nhiệm về một khía cạnh cụ thể của quy trình review code. Các TEAM này sẽ tương tác và phối hợp nhịp nhàng với nhau dưới sự điều phối của một **Orchestrator Agent** trung tâm.

### **2.1. Sơ đồ Tương tác Tổng quan giữa các TEAM Agent:**

graph TD  
    UI\[User Interface (CLI/Web \- vd: Streamlit)\] \--\> Orchestrator;  
    Orchestrator \--\> TI\[TEAM Interaction & Tasking\];  
    TI \--\> Orchestrator;  
    Orchestrator \--\> TDA\[TEAM Data Acquisition\];  
    TDA \--\> Orchestrator;  
    Orchestrator \--\> TCKG\[TEAM CKG Operations\];  
    TCKG \--\> Orchestrator;  
    TCKG \--\> TDA;   
    TCKG \--\> TCA;  
    Orchestrator \--\> TCA\[TEAM Code Analysis\];  
    TCA \--\> Orchestrator;  
    TCA \--\> TLLM\[TEAM LLM Services\];  
    TLLM \--\> TCA;  
    Orchestrator \--\> TSR\[TEAM Synthesis & Reporting\];  
    TSR \--\> Orchestrator;  
    TSR \--\> TLLM;  
    TSR \--\> TI;

    subgraph AI CodeScan Core System  
        direction LR  
        Orchestrator;  
        subgraph UserFacingAgents  
            TI;  
        end  
        subgraph DataProcessingAgents  
            TDA;  
            TCKG;  
            TCA;  
        end  
        subgraph ServiceAgents  
            TLLM;  
        end  
        subgraph OutputAgents  
            TSR;  
        end  
    end

    style Orchestrator fill:\#daffc4,stroke:\#333,stroke-width:2px  
    style TI fill:\#c4e4ff,stroke:\#333,stroke-width:2px  
    style TDA fill:\#c4e4ff,stroke:\#333,stroke-width:2px  
    style TCKG fill:\#fff5c4,stroke:\#333,stroke-width:2px  
    style TCA fill:\#fff5c4,stroke:\#333,stroke-width:2px  
    style TLLM fill:\#ffc4c4,stroke:\#333,stroke-width:2px  
    style TSR fill:\#e6c4ff,stroke:\#333,stroke-width:2px

### **2.2. Các TEAM Agent chính bao gồm:**

1. **TEAM Interaction & Tasking (Đội Tương tác & Quản lý Tác vụ)**  
2. **TEAM Data Acquisition (Đội Thu thập & Chuẩn bị Dữ liệu)**  
3. **TEAM CKG Operations (Đội Vận hành Code Knowledge Graph)**  
4. **TEAM Code Analysis (Đội Phân tích Mã nguồn)**  
5. **TEAM LLM Services (Đội Dịch vụ LLM)**  
6. **TEAM Synthesis & Reporting (Đội Tổng hợp & Báo cáo)**

## **Phần III: Thiết kế Chi tiết các TEAM Agent**

### **A. Orchestrator Agent (Agent Điều phối Trung tâm)**

1. Mục tiêu chung:  
   Điều phối tổng thể luồng công việc, quản lý tác vụ và đảm bảo sự tương tác trơn tru và hiệu quả giữa tất cả các TEAM agent trong hệ thống AI CodeScan.  
2. **Trách nhiệm chính:**  
   * Tiếp nhận yêu cầu tác vụ đã được chuẩn hóa từ TEAM Interaction & Tasking.  
   * Kích hoạt các TEAM agent theo đúng trình tự logic của một phiên review code (ví dụ: Data Acquisition \-\> CKG Operations \-\> Code Analysis \-\> Synthesis & Reporting).  
   * Quản lý trạng thái (pending, running, completed, failed) của tác vụ review tổng thể và của từng bước do các TEAM thực hiện.  
   * Đảm bảo dữ liệu (inputs/outputs) được chuyển giao chính xác và kịp thời giữa các TEAM.  
   * Xử lý các ngoại lệ, lỗi phát sinh từ các TEAM ở cấp độ luồng công việc và quyết định các hành động khắc phục (ví dụ: thử lại, báo lỗi cho người dùng).  
3. **Input chính:**  
   * TaskDefinition object (định nghĩa tác vụ review chi tiết) từ TEAM Interaction & Tasking.  
   * Thông điệp cập nhật trạng thái và kết quả từ các TEAM agent khác.  
4. **Output chính:**  
   * Lệnh kích hoạt (activation commands) và dữ liệu đầu vào cho các TEAM agent.  
   * Thông tin cập nhật về trạng thái và tiến trình của tác vụ cho TEAM Interaction & Tasking (để hiển thị cho người dùng).  
   * Thông báo lỗi hoặc kết quả cuối cùng của tác vụ.  
5. **Thành** viên Agent (Đây là một agent điều phối logic, có **thể không có "member agents" theo nghĩa truyền thống, mà là các module chức năng):**  
   * **WorkflowEngineModule**  
     * **Mục tiêu:** Thực thi các luồng công việc đã được định nghĩa.  
     * **Trách nhiệm:** Dựa trên TaskDefinition, điều phối các bước, gọi các TEAM agent tương ứng.  
     * **Input:** TaskDefinition, quy tắc luồng công việc.  
     * **Output:** Lệnh gọi các TEAM.  
     * **Công nghệ đề xuất:** LangGraph có thể được xem xét để định nghĩa và thực thi workflow.  
   * **StateManagerModule**  
     * **Mục tiêu:** Theo dõi trạng thái của toàn bộ tác vụ và các bước con.  
     * **Trách nhiệm:** Cập nhật trạng thái dựa trên thông báo từ các TEAM.  
     * **Input:** Thông điệp trạng thái từ các TEAM.  
     * **Output:** Trạng thái hiện tại của tác vụ.  
   * **ErrorHandlingModule**  
     * **Mục tiêu:** Xử lý lỗi một cách nhất quán.  
     * **Trách nhiệm:** Bắt lỗi từ các TEAM, quyết định hành động (retry, abort, notify).  
     * **Input:** Thông điệp lỗi.  
     * **Output:** Hành động xử lý lỗi, thông báo lỗi.  
6. **Công cụ (Tools) / Giao thức Đa Ngữ cảnh (MCPs) cần phát triển:**  
   * **Task Definition Protocol (TDP):** Định dạng chuẩn (ví dụ: JSON Schema) cho việc mô tả một tác vụ review (bao gồm repo URL, PR ID, loại phân tích yêu cầu, ngôn ngữ ưu tiên, cấu hình PAT, etc.).  
   * **Agent State Communication Protocol (ASCP):** Giao thức chuẩn để các TEAM báo cáo trạng thái (ví dụ: PENDING, RUNNING, COMPLETED, FAILED\_RETRYABLE, FAILED\_PERMANENT) và kết quả (hoặc con trỏ tới kết quả) cho Orchestrator.  
   * **Workflow Definition Language (nếu cần):** Một cách để định nghĩa các luồng công việc phức tạp (có thể tận dụng khả năng của LangGraph).  
7. **Cơ chế Phối hợp:**  
   * Là trung tâm điều phối, Orchestrator nhận yêu cầu từ TEAM Interaction & Tasking.  
   * Tuần tự hoặc song song hóa việc gọi các TEAM: TDA \-\> TCKG \-\> TCA \-\> TSR.  
   * TCA và TSR có thể yêu cầu dịch vụ từ TLLM thông qua Orchestrator hoặc một cơ chế đăng ký dịch vụ.  
   * Liên tục cập nhật trạng thái cho TEAM Interaction & Tasking.  
8. **Chủ đề Nghiên cứu Chuyên sâu (Gemini Deep Research Topics):**  
   * **Adaptive and Dynamic Workflow Orchestration:** Làm thế nào Orchestrator có thể tự động điều chỉnh và tối ưu hóa luồng công việc dựa trên đặc điểm của từng project (ví dụ: kích thước, ngôn ngữ, loại thay đổi trong PR) hoặc dựa trên kết quả phân tích ban đầu từ các TEAM?  
   * **Advanced Fault Tolerance and Recovery Strategies:** Phát triển các chiến lược mạnh mẽ cho Orchestrator để xử lý lỗi từ các TEAM agent (ví dụ: timeout, lỗi tài nguyên, lỗi logic của agent) và có khả năng phục hồi quy trình một cách thông minh, giảm thiểu gián đoạn cho người dùng.  
   * **Resource Management for Concurrent Tasks:** Nếu hệ thống hỗ trợ nhiều người dùng hoặc nhiều tác vụ review đồng thời, Orchestrator cần quản lý tài nguyên (CPU, memory, API rate limits cho LLM) như thế nào để đảm bảo hiệu suất và sự ổn định?

### **B. TEAM Interaction & Tasking (Đội Tương tác & Quản lý Tác vụ)**

1. Mục tiêu chung của TEAM:  
   Là giao diện chính và bộ não giao tiếp của AI CodeScan với người dùng. Đảm bảo mọi yêu cầu của người dùng được hiểu chính xác, chuyển thành các tác vụ có cấu trúc cho hệ thống, và người dùng luôn được thông báo một cách rõ ràng, kịp thời về tiến trình cũng như kết quả.  
2. **Trách nhiệm chính của TEAM:**  
   * Tiếp nhận và phân tích yêu cầu dưới dạng ngôn ngữ tự nhiên từ người dùng thông qua các kênh giao tiếp (CLI, Web UI \- ví dụ: Streamlit).  
   * Quản lý và duy trì luồng hội thoại một cách mạch lạc, đặt các câu hỏi làm rõ khi thông tin cung cấp chưa đủ hoặc mơ hồ.  
   * Chuyển đổi yêu cầu đã được làm rõ của người dùng thành một TaskDefinition object chuẩn hóa, sẵn sàng để Orchestrator xử lý.  
   * Tiếp nhận và hiển thị các kết quả, báo cáo, sơ đồ, và thông báo trạng thái từ hệ thống cho người dùng một cách trực quan và dễ hiểu.  
   * Quản lý trạng thái của phiên tương tác người dùng (ví dụ: repo đang làm việc, lịch sử các câu hỏi gần đây, các thiết lập ưu tiên của người dùng).  
3. **Input** chính của **TEAM:**  
   * Phát ngôn (text, commands) của người dùng từ giao diện.  
   * Thông tin trạng thái tác vụ, thông báo lỗi, và kết quả/báo cáo cuối cùng từ Orchestrator (do các TEAM khác tạo ra).  
   * Lịch sử hội thoại của phiên làm việc hiện tại.  
4. **Output chính của TEAM:**  
   * TaskDefinition object chuẩn hóa, được gửi đến Orchestrator.  
   * Các câu hỏi làm rõ, thông báo xác nhận, thông báo trạng thái gửi đến người dùng.  
   * Hiển thị báo cáo review, sơ đồ kiến trúc, và các câu trả lời Q\&A cho người dùng.  
5. **Thành viên Agent trong TEAM:**  
   * **UserIntentParserAgent (Agent Phân tích Ý định Người dùng)**  
     * **Mục tiêu:** Phân tích và hiểu chính xác ý định cũng như các tham số quan trọng trong yêu cầu của người dùng.  
     * **Trách nhiệm:** Sử dụng các kỹ thuật NLU để phân tích văn bản đầu vào từ người dùng, trích xuất các thực thể như loại hành động (review project, review PR, hỏi đáp, yêu cầu sơ đồ), tên repository, ID của Pull Request, nội dung câu hỏi cụ thể, tên class/module cần vẽ sơ đồ, etc.  
     * **Input:** Phát ngôn thô của người dùng, có thể kèm theo ngữ cảnh hội thoại.  
     * **Output:** Một cấu trúc dữ liệu chuẩn hóa biểu diễn ý định và các tham số của người dùng (ví dụ: JSON: { "intent": "review\_pr", "entities": { "repo\_url": "https://github.com/user/repo", "pr\_id": "123" } }).  
     * **Công nghệ đề xuất:** spaCy, RASA NLU, hoặc API NLU của LLM (OpenAI).  
   * **DialogManagerAgent (Agent Quản lý Hội thoại)**  
     * **Mục tiêu:** Duy trì một cuộc hội thoại tự nhiên, mạch lạc và hiệu quả với người dùng, hướng tới việc thu thập đủ thông tin cho một tác vụ.  
     * **Trách nhiệm:** Dựa trên ý định đã được phân tích (từ UserIntentParserAgent) và lịch sử hội thoại, quyết định hành động tiếp theo: đặt câu hỏi làm rõ nếu thiếu thông tin, xác nhận lại thông tin đã hiểu, cung cấp hướng dẫn, hoặc thông báo khi bắt đầu một tác vụ. Quản lý ngữ cảnh hội thoại.  
     * **Input:** Output từ UserIntentParserAgent, lịch sử hội thoại, trạng thái hệ thống (nếu cần).  
     * **Output:** Thông điệp/câu hỏi được định dạng để gửi đến người dùng qua giao diện.  
   * **TaskInitiationAgent (Agent Khởi tạo Tác vụ)**  
     * **Mục tiêu:** Tạo ra một TaskDefinition hoàn chỉnh sau khi đã có đủ thông tin từ người dùng.  
     * **Trách nhiệm:** Tổng hợp tất cả thông tin đã được xác nhận từ DialogManagerAgent để tạo thành một TaskDefinition object theo TDP (Task Definition Protocol).  
     * **Input:** Toàn bộ thông tin cần thiết cho một tác vụ đã được xác nhận (repo, PR, loại review, etc.).  
     * **Output:** TaskDefinition object gửi cho Orchestrator.  
   * **PresentationAgent (Agent Trình bày Thông tin)**  
     * **Mục tiêu:** Hiển thị kết quả và thông tin từ hệ thống cho người dùng một cách rõ ràng và hữu ích.  
     * **Trách nhiệm:** Nhận báo cáo, sơ đồ (dạng mã PlantUML/Mermaid hoặc ảnh), câu trả lời Q\&A, thông báo lỗi từ Orchestrator và định dạng chúng để hiển thị phù hợp trên giao diện người dùng (CLI, Web \- vd: Streamlit).  
     * **Input:** Dữ liệu kết quả (báo cáo, sơ đồ, text) từ Orchestrator.  
     * **Output:** Nội dung được hiển thị trên UI.  
     * **Công nghệ đề xuất:** Streamlit cho giao diện web, thư viện CLI (vd: click trong Python).  
6. **Công cụ (Tools) / Giao thức Đa Ngữ cảnh (MCPs) cần phát triển cho TEAM:**  
   * **Natural Language Understanding (NLU) Service:** Một module NLU mạnh mẽ (có thể sử dụng thư viện như spaCy, RASA NLU, hoặc các API NLU của LLM).  
   * **Intent Schema & Entity Definition MCP:** Định dạng chuẩn (ví dụ: JSON Schema) cho việc biểu diễn ý định người dùng và các thực thể đã được trích xuất.  
   * **Dialog State Management Protocol:** Giao thức để theo dõi và quản lý trạng thái của cuộc hội thoại (ví dụ: lượt hiện tại, các thông tin đã thu thập, câu hỏi đang chờ trả lời).  
   * **User Interface Abstraction Layer:** Một lớp để PresentationAgent có thể gửi output đến các loại UI khác nhau (CLI, Web) mà không cần biết chi tiết cụ thể của từng UI.  
   * **Session Memory Access:** Giao diện để truy cập bộ nhớ session (ví dụ: Mem0 hoặc giải pháp tương tự) để lưu/tải lịch sử hội thoại, thông tin PAT tạm thời (chỉ trong session).  
7. **Cơ chế Phối hợp:**  
   * Là điểm bắt đầu và kết thúc của mọi tương tác với người dùng.  
   * UserIntentParserAgent và DialogManagerAgent phối hợp chặt chẽ để làm rõ yêu cầu.  
   * Khi đủ thông tin, TaskInitiationAgent tạo TaskDefinition và gửi cho Orchestrator.  
   * PresentationAgent nhận dữ liệu từ Orchestrator (do TEAM Synthesis & Reporting hoặc các TEAM khác cung cấp) để hiển thị.  
   * Liên tục nhận cập nhật trạng thái từ Orchestrator để thông báo cho người dùng thông qua DialogManagerAgent hoặc PresentationAgent.  
8. **Chủ đề Nghiên cứu Chuyên sâu (Gemini Deep Research Topics):**  
   * **Advanced NLU for Developer Queries:** Phát triển hoặc tích hợp các kỹ thuật NLU có khả năng hiểu sâu các truy vấn phức tạp, thuật ngữ kỹ thuật đặc thù, và ngữ cảnh ngầm trong các yêu cầu của nhà phát triển liên quan đến review code.  
   * **Proactive and Context-Aware Dialog Management:** Làm thế nào DialogManagerAgent có thể chủ động đưa ra các gợi ý hữu ích, dự đoán nhu cầu tiếp theo của người dùng, hoặc đề xuất các loại phân tích phù hợp dựa trên ngữ cảnh của codebase hoặc các tương tác trước đó?  
   * **Personalized User Experience:** Nghiên cứu cách hệ thống có thể học hỏi từ lịch sử tương tác và phản hồi của từng người dùng để cá nhân hóa giao tiếp, các loại báo cáo được ưu tiên, hoặc các thiết lập review mặc định.  
   * **Multi-modal Interaction (Future):** Nghiên cứu khả năng tích hợp các kênh tương tác khác ngoài text (ví dụ: giọng nói, hoặc tương tác trực tiếp trên sơ đồ được hiển thị) cho các phiên bản tương lai.

### **C. TEAM Data Acquisition (Đội Thu thập & Chuẩn bị Dữ liệu)**

1. Mục tiêu chung của TEAM:  
   Đảm bảo thu thập mã nguồn, thông tin Pull Request (nếu có), và các siêu dữ liệu liên quan một cách chính xác, hiệu quả và an toàn từ các nguồn được chỉ định. Đồng thời, xác định môi trường ngôn ngữ của dự án để cung cấp đầu vào đã được chuẩn bị cho các TEAM phân tích và xây dựng CKG.  
2. **Trách nhiệm chính của TEAM:**  
   * Thực hiện shallow clone repository từ URL được cung cấp, hoặc tải xuống chi tiết của một Pull Request cụ thể (bao gồm diffs, metadata như title, description, comments).  
   * Quản lý việc yêu cầu và sử dụng Personal Access Token (PAT) một cách an toàn và tạm thời cho việc truy cập các private repositories (chỉ khi cần thiết và không lưu trữ bền vững).  
   * Xác định (các) ngôn ngữ lập trình chính được sử dụng trong codebase (Java, Kotlin, Dart, Python cho v1.0) và có thể cả các framework/thư viện chủ đạo.  
   * Chuẩn bị và cấu trúc toàn bộ dữ liệu đã thu thập (đường dẫn đến mã nguồn đã clone, thông tin PR, danh sách ngôn ngữ đã xác định) theo một định dạng chuẩn ("ProjectDataContext") để các TEAM khác có thể sử dụng.  
3. **Input chính của TEAM:**  
   * TaskDefinition object từ Orchestrator, chứa thông tin như:  
     * URL của repository.  
     * (Tùy chọn) ID của Pull Request.  
     * Thông tin về việc có thể cần PAT (ví dụ: nếu là private repo).  
     * (Tùy chọn) Các nhánh (branches) hoặc commit hashes cụ thể cần phân tích (cho v1.0 là HEAD).  
4. **Output chính của TEAM:**  
   * Một ProjectDataContext object/structure chuẩn hóa, chứa:  
     * Đường dẫn đến mã nguồn đã được clone trên hệ thống file tạm thời.  
     * Dữ liệu chi tiết của Pull Request (diffs, metadata) nếu tác vụ là review PR.  
     * Danh sách các ngôn ngữ lập trình và (có thể) các framework chính đã được xác định trong project.  
     * Một session ID hoặc định danh cho dữ liệu tạm thời này để quản lý.  
5. **Thành viên Agent trong TEAM:**  
   * **GitOperationsAgent (Agent Thao tác Git)**  
     * **Mục tiêu:** Thực hiện các thao tác với Git (clone, fetch PR details) một cách hiệu quả, an toàn và tuân thủ các yêu cầu (ví dụ: shallow clone).  
     * **Trách nhiệm:**  
       * Thực hiện git clone \--depth 1 cho repository được chỉ định.  
       * Nếu review PR, fetch thông tin chi tiết của PR (diffs, commit details, title, description, comments từ platform như GitHub/GitLab) sử dụng PAT (nếu được PATHandlerAgent cung cấp).  
     * **Input:** URL Repository, (tùy chọn) PR ID, (tùy chọn) PAT, cấu hình clone (ví dụ: depth).  
     * **Output:** Đường dẫn đến mã nguồn đã clone trên hệ thống file cục bộ, dữ liệu PR thô (ví dụ: JSON từ API của Git platform).  
     * **Công nghệ đề xuất:** Thư viện gitpython (Python).  
   * **PATHandlerAgent (Agent Xử lý PAT)**  
     * **Mục tiêu:** Quản lý quy trình yêu cầu và sử dụng PAT một cách an toàn, chỉ khi thực sự cần thiết và trong thời gian ngắn nhất.  
     * **Trách nhiệm:**  
       * Khi GitOperationsAgent báo cáo cần PAT (ví dụ: clone private repo thất bại), agent này sẽ kích hoạt một quy trình (thông qua Orchestrator \-\> TEAM Interaction & Tasking) để yêu cầu PAT từ người dùng.  
       * Lưu trữ PAT một cách an toàn trong bộ nhớ session (ví dụ: sử dụng Mem0) chỉ trong thời gian cần thiết cho thao tác Git.  
       * Cung cấp PAT cho GitOperationsAgent.  
       * Đảm bảo PAT được xóa khỏi bộ nhớ session ngay sau khi thao tác Git hoàn tất hoặc phiên làm việc kết thúc.  
     * **Input:** Yêu cầu cần PAT từ GitOperationsAgent hoặc Orchestrator.  
     * **Output:** PAT (cho GitOperationsAgent), trạng thái (thành công/thất bại trong việc thu thập PAT).  
   * **LanguageIdentifierAgent (Agent Định danh Ngôn ngữ & Framework)**  
     * **Mục tiêu:** Xác định chính xác và hiệu quả các ngôn ngữ lập trình và các framework/thư viện chủ đạo được sử dụng trong codebase đã clone.  
     * **Trách nhiệm:**  
       * Phân tích cấu trúc thư mục của project.  
       * Kiểm tra phần mở rộng của các file mã nguồn.  
       * Phân tích nội dung của các file cấu hình dự án đặc thù (ví dụ: pom.xml, build.gradle cho Java/Kotlin; pubspec.yaml cho Dart/Flutter; requirements.txt, Pipfile, pyproject.toml cho Python).  
     * **Input:** Đường dẫn đến mã nguồn đã clone trên hệ thống file cục bộ.  
     * **Output:** Một danh sách các ngôn ngữ và (nếu có thể) các framework/thư viện chính được phát hiện (ví dụ: {"languages": \["java", "kotlin", "python"\], "frameworks": \["spring\_boot", "flask"\]}).  
     * **Công nghệ đề xuất:** python-linguist hoặc heuristics tùy chỉnh.  
   * **DataPreparationAgent (Agent Chuẩn bị và Đóng gói Dữ liệu)**  
     * **Mục tiêu:** Đảm bảo tất cả dữ liệu thu thập được đóng gói một cách nhất quán và chuẩn hóa trước khi chuyển cho các TEAM khác.  
     * **Trách nhiệm:**  
       * Tập hợp output từ GitOperationsAgent (đường dẫn code, dữ liệu PR) và LanguageIdentifierAgent (danh sách ngôn ngữ/framework).  
       * Đóng gói các thông tin này vào một ProjectDataContext object/structure theo schema đã định.  
     * **Input:** Đường dẫn code đã clone, dữ liệu PR thô, danh sách ngôn ngữ/framework.  
     * **Output:** ProjectDataContext object/structure hoàn chỉnh.  
6. **Công cụ (Tools) / Giao thức Đa Ngữ cảnh (MCPs) cần phát triển cho TEAM:**  
   * **Git Interaction Libraries:** Tận dụng các thư viện mã nguồn mở như gitpython (Python).  
   * **Git Platform API Clients:** Thư viện như PyGithub (Python cho GitHub) hoặc các thư viện tương tự cho GitLab, Bitbucket để lấy thông tin PR.  
   * **PAT Request & Handling Protocol (PRHP):** Một MCP định nghĩa cách PATHandlerAgent giao tiếp với TEAM Interaction & Tasking (thông qua Orchestrator) để yêu cầu và nhận PAT một cách an toàn, bao gồm cả cơ chế timeout và xử lý lỗi.  
   * **Language & Framework Detection Engine:** Có thể sử dụng các công cụ mã nguồn mở như python-linguist (của GitHub) hoặc phát triển các heuristics và bộ quy tắc tùy chỉnh dựa trên phân tích file cấu hình và cấu trúc thư mục.  
   * **ProjectDataContext Schema (PDCS):** Một schema JSON hoặc cấu trúc object được định nghĩa rõ ràng cho ProjectDataContext để đảm bảo tính nhất quán khi truyền dữ liệu giữa các TEAM.  
7. **Cơ chế Phối hợp:**  
   * Nhận TaskDefinition từ Orchestrator.  
   * Nếu tác vụ yêu cầu truy cập private repo và PAT chưa có hoặc không hợp lệ, PATHandlerAgent sẽ phối hợp với Orchestrator và TEAM Interaction & Tasking để lấy PAT từ người dùng.  
   * Sau khi GitOperationsAgent clone code và LanguageIdentifierAgent xác định ngôn ngữ, DataPreparationAgent sẽ đóng gói ProjectDataContext.  
   * Gửi ProjectDataContext hoàn chỉnh cho Orchestrator. Orchestrator sau đó sẽ chuyển tiếp dữ liệu này cho TEAM CKG Operations để bắt đầu quá trình xây dựng CKG.  
8. **Chủ đề Nghiên cứu Chuyên sâu (Gemini Deep Research Topics):**  
   * **Advanced Language & Framework Detection:** Phát triển các kỹ thuật (có thể ứng dụng Machine Learning) để xác định chính xác hơn không chỉ các ngôn ngữ và framework chính, mà còn cả các thư viện quan trọng, phiên bản của chúng, và các cấu hình đặc thù trong các project phức tạp, đa ngôn ngữ, hoặc có cấu trúc không theo chuẩn mực thông thường.  
   * **Efficient Handling of Very Large Repositories (Monorepos):** Ngoài việc sử dụng shallow clone, nghiên cứu các chiến lược khác (ví dụ: sparse checkout để chỉ clone các phần cần thiết, phân tích theo từng module/sub-project được người dùng yêu cầu) để xử lý hiệu quả các monorepo hoặc codebase cực lớn mà không gây quá tải cho hệ thống về thời gian và tài nguyên.  
   * **Secure and Auditable PAT Management in Multi-Agent Systems:** Nghiên cứu các giải pháp SOTA (State-Of-The-Art) cho việc xử lý thông tin nhạy cảm như PAT trong một hệ thống phân tán, đảm bảo an toàn tuyệt đối ngay cả trong bộ nhớ session, và có khả năng ghi lại nhật ký (audit log) việc sử dụng PAT một cách an toàn.  
   * **Delta Code Fetching for PR Reviews:** Đối với review PR, thay vì clone toàn bộ HEAD rồi áp diff, nghiên cứu cách chỉ fetch các file bị ảnh hưởng và lịch sử liên quan trực tiếp đến PR để tối ưu hơn nữa.

### **D. TEAM CKG Operations (Đội Vận hành Code Knowledge Graph)**

1. Mục tiêu chung của TEAM:  
   Xây dựng, duy trì, cập nhật và cung cấp một Code Knowledge Graph (CKG) chính xác, toàn diện và dễ truy vấn làm nền tảng tri thức trung tâm cho toàn bộ hệ thống AI CodeScan. CKG là "bộ não" lưu trữ hiểu biết cấu trúc và ngữ nghĩa của mã nguồn.  
2. **Trách nhiệm chính của TEAM:**  
   * Tiếp nhận dữ liệu mã nguồn đã được chuẩn bị (từ TEAM Data Acquisition).  
   * Thực hiện phân tích cú pháp (parsing) mã nguồn của các ngôn ngữ được hỗ trợ (Java, Kotlin, Dart, Python cho v1.0) để tạo ra Abstract Syntax Trees (ASTs).  
   * Trích xuất các thực thể code (files, classes, functions/methods, variables, interfaces, enums, etc.) và các mối quan hệ quan trọng giữa chúng (lời gọi hàm/method, kế thừa, hiện thực hóa, import/dependencies, chứa đựng, etc.) từ ASTs và các siêu dữ liệu khác.  
   * Xây dựng (hoặc cập nhật) CKG bằng cách lưu trữ các thực thể và mối quan hệ này vào một graph database (Neo4j Community Edition cho v1.0).  
   * Cung cấp một giao diện/API chuẩn hóa và hiệu quả cho các TEAM khác (chủ yếu là TEAM Code Analysis) để truy vấn thông tin từ CKG.  
   * (Lộ trình tương lai) Quản lý phiên bản của CKG và thực hiện cập nhật CKG một cách tăng tiến khi có thay đổi trong mã nguồn.  
3. **Input chính của TEAM:**  
   * ProjectDataContext object từ TEAM Data Acquisition (thông qua Orchestrator), chứa đường dẫn đến mã nguồn đã clone và danh sách các ngôn ngữ/framework đã được xác định.  
   * (Tương lai) Thông tin về các thay đổi (diffs) trong mã nguồn để thực hiện cập nhật tăng tiến.  
4. **Output chính của TEAM:**  
   * Một Code Knowledge Graph đã được xây dựng hoặc cập nhật trong graph database (Neo4j), sẵn sàng để truy vấn.  
   * Một giao diện/API truy vấn CKG (ví dụ: một tập hợp các hàm/dịch vụ để lấy thông tin cụ thể từ CKG).  
   * Thông báo trạng thái về quá trình xây dựng/cập nhật CKG (thành công, thất bại, các cảnh báo về parsing hoặc trích xuất dữ liệu).  
5. **Thành viên Agent trong TEAM:**  
   * **CodeParserCoordinatorAgent (Agent Điều phối Phân tích Cú pháp)**  
     * **Mục tiêu:** Quản lý và điều phối hiệu quả quá trình parsing cho các ngôn ngữ lập trình khác nhau có trong project.  
     * **Trách nhiệm:**  
       * Dựa trên danh sách ngôn ngữ từ ProjectDataContext, lựa chọn và kích hoạt các parser chuyên biệt phù hợp.  
       * Quản lý việc phân tích song song các file code (nếu có thể).  
       * Thu thập kết quả là các Abstract Syntax Trees (ASTs) hoặc các cấu trúc dữ liệu tương đương từ các parser.  
     * **Input:** ProjectDataContext (đặc biệt là đường dẫn code và danh sách ngôn ngữ).  
     * **Output:** Một tập hợp các ASTs (hoặc cấu trúc dữ liệu tương đương) cho các file code liên quan, cùng với thông tin về ngôn ngữ của từng file.  
     * **Công nghệ đề xuất:**  
       * Java: javaparser library.  
       * Kotlin: Khai thác Kotlin Compiler API hoặc Detekt (để truy cập AST).  
       * Dart: analyzer package từ Dart SDK.  
       * Python: Module ast tích hợp sẵn.  
   * **ASTtoCKGBuilderAgent (Agent Xây dựng CKG từ AST)**  
     * **Mục tiêu:** Chuyển đổi chính xác và nhất quán thông tin cấu trúc và ngữ nghĩa từ các ASTs thành các nodes và relationships trong Code Knowledge Graph.  
     * **Trách nhiệm:**  
       * Duyệt qua các ASTs đã được cung cấp.  
       * Áp dụng các quy tắc để xác định và trích xuất các thực thể code và các mối quan hệ theo schema CKG đã được định nghĩa.  
       * Tạo các lệnh truy vấn (ví dụ: Cypher cho Neo4j) để tạo mới hoặc cập nhật các nodes và relationships trong graph database.  
     * **Input:** Tập hợp ASTs từ CodeParserCoordinatorAgent, CKG Schema.  
     * **Output:** Các lệnh thực thi trên graph database (ví dụ: Cypher queries), trạng thái ghi dữ liệu (thành công/lỗi cho từng phần).  
     * **Công nghệ đề xuất:** Neo4j Community Edition, Cypher query language.  
   * **CKGQueryInterfaceAgent (Agent Cung cấp Giao diện Truy vấn CKG)**  
     * **Mục tiêu:** Cung cấp một cách thức chuẩn hóa, hiệu quả và dễ sử dụng để các agent khác có thể truy vấn thông tin từ CKG mà không cần biết chi tiết về graph database bên dưới.  
     * **Trách nhiệm:**  
       * Định nghĩa và triển khai một tập hợp các hàm/API truy vấn CKG phổ biến và cần thiết cho các tác vụ phân tích (ví dụ: getClassDefinition(className), findCallers(functionName), getDependencies(moduleName), getInheritanceHierarchy(className)).  
       * Tối ưu hóa các truy vấn này để đảm bảo hiệu năng.  
       * (Có thể) Quản lý caching cho các truy vấn thường xuyên.  
     * **Input:** Yêu cầu truy vấn CKG (được định dạng theo API đã định nghĩa) từ TEAM Code Analysis hoặc các TEAM khác.  
     * **Output:** Kết quả truy vấn CKG (thường ở dạng JSON, list of objects, hoặc một cấu trúc dữ liệu phù hợp).  
6. **Công cụ (Tools) / Giao thức Đa Ngữ cảnh (MCPs) cần phát triển cho TEAM:**  
   * **Bộ Parsers chuyên biệt cho từng ngôn ngữ (v1.0):** (Đã liệt kê ở trên)  
   * **CKG Schema Definition (CKGSD):** Một tài liệu hoặc file (ví dụ: YAML, JSON Schema) mô tả chi tiết cấu trúc các loại node, loại relationship, và các thuộc tính (properties) của chúng trong CKG. Điều này đảm bảo tính nhất quán.  
   * **AST-to-CKG Mapping Rules:** Bộ quy tắc (có thể được code hóa) định nghĩa cách ASTtoCKGBuilderAgent chuyển đổi các thành phần từ AST của từng ngôn ngữ thành các thực thể và mối quan hệ trong CKG theo CKGSD.  
   * **CKG Query API Specification:** Định nghĩa chi tiết các endpoints hoặc hàm của CKGQueryInterfaceAgent, bao gồm tham số đầu vào và định dạng đầu ra.  
   * **Graph Database Client/Driver:** Ví dụ: neo4j Python driver để tương tác với Neo4j.  
7. **Cơ chế Phối hợp:**  
   * Nhận ProjectDataContext từ Orchestrator (do TEAM Data Acquisition cung cấp).  
   * CodeParserCoordinatorAgent điều phối việc parsing.  
   * ASTtoCKGBuilderAgent xây dựng hoặc cập nhật CKG.  
   * Sau khi hoàn tất, thông báo trạng thái xây dựng CKG cho Orchestrator.  
   * CKGQueryInterfaceAgent hoạt động như một service, đáp ứng các yêu cầu truy vấn CKG từ TEAM Code Analysis (các yêu cầu này có thể được điều phối qua Orchestrator hoặc là tương tác trực tiếp tùy theo thiết kế chi tiết của message bus/service discovery).  
8. **Chủ đề Nghiên cứu Chuyên sâu (Gemini Deep Research Topics):**  
   * **Tối ưu Schema CKG cho Phân tích Đa Ngôn ngữ và Sâu:** Nghiên cứu và đề xuất một schema CKG hợp nhất, linh hoạt nhưng chi tiết, có khả năng biểu diễn chính xác và đầy đủ các khía cạnh ngữ nghĩa của mã nguồn từ các ngôn ngữ Java, Kotlin, Dart, Python. Schema này cần hỗ trợ hiệu quả các truy vấn phức tạp cho phân tích kiến trúc, luồng dữ liệu, và các mối quan hệ ngầm.  
   * **Xây dựng CKG Tăng tiến (Incremental CKG Updates) Hiệu quả:** Phát triển các thuật toán và kiến trúc cho phép cập nhật CKG một cách thông minh và nhanh chóng chỉ dựa trên những thay đổi (diffs) của mã nguồn, thay vì phải parse lại toàn bộ project sau mỗi thay đổi nhỏ. Điều này cực kỳ quan trọng cho hiệu năng với các project lớn và tích hợp CI/CD.  
   * **Kỹ thuật Semantic Enrichment cho CKG:** Nghiên cứu các kỹ thuật (bao gồm cả Machine Learning, LLM, hoặc các phương pháp phân tích tĩnh tiên tiến) để tự động làm giàu CKG với các thông tin ngữ nghĩa ở mức độ cao hơn như: suy luận kiểu dữ liệu chính xác hơn (advanced type inference), phát hiện các design pattern cụ thể, liên kết các đoạn code với các yêu cầu nghiệp vụ hoặc tài liệu thiết kế.  
   * **So sánh và Đánh giá các Graph Databases Mã nguồn mở cho CKG:** Ngoài Neo4j Community Edition, thực hiện đánh giá sâu hơn về các lựa chọn graph database mã nguồn mở khác (ví dụ: JanusGraph, ArangoDB, TigerGraph, Memgraph) về các mặt: hiệu năng cho các loại truy vấn CKG đặc thù, khả năng mở rộng, tính năng truy vấn đồ thị, sự trưởng thành của hệ sinh thái, và sự phù hợp tổng thể cho việc lưu trữ và vận hành CKG của AI CodeScan.  
   * **Version Control cho CKG:** Nghiên cứu các phương pháp để quản lý phiên bản của CKG, tương ứng với các phiên bản của mã nguồn, cho phép "du hành thời gian" trên CKG hoặc so sánh các phiên bản CKG khác nhau.

### **E. TEAM Code Analysis (Đội Phân tích Mã nguồn)**

1. Mục tiêu chung của TEAM:  
   Thực hiện các phân tích chuyên sâu và đa dạng trên mã nguồn đã được biểu diễn trong CKG, kết hợp với khả năng suy luận của LLM, để phát hiện các vấn đề tiềm ẩn, các điểm cần cải thiện về kiến trúc, chất lượng code, và cung cấp các hiểu biết giá trị cho người dùng.  
2. **Trách nhiệm chính của TEAM (v1.0):**  
   * Truy vấn CKG một cách hiệu quả để thu thập thông tin cấu trúc, mối quan hệ và siêu dữ liệu cần thiết cho các tác vụ phân tích.  
   * **Thực hiện Phân tích Kiến trúc (Cơ bản):**  
     * Phát hiện các circular dependencies ở cấp độ file/module.  
     * Đưa ra gợi ý về các public methods/classes có khả năng không được sử dụng từ bên ngoài module của chúng trong phạm vi codebase đã phân tích (với các cảnh báo về hạn chế của phương pháp).  
   * **Tích hợp và Điều phối việc chạy các Linter/Static Analyzer:** Kích hoạt các công cụ linter/static analyzer tiêu chuẩn cho từng ngôn ngữ (Checkstyle, PMD, Detekt, Ktlint, Dart Analyzer, Flake8, Pylint) và thu thập, chuẩn hóa kết quả của chúng.  
   * **Chuẩn bị Ngữ cảnh cho Phân tích Logic & Q\&A bởi LLM:** Trích xuất các đoạn code liên quan, thông tin ngữ cảnh từ CKG để TEAM LLM Services có thể hỗ trợ trả lời các câu hỏi cụ thể của người dùng hoặc thực hiện các phân tích sâu hơn về một đoạn code.  
   * (Lộ trình tương lai) Phát hiện các anti-pattern kiến trúc phức tạp hơn, phân tích các vấn đề bảo mật cơ bản, đánh giá sâu hơn về khả năng bảo trì.  
3. **Input chính của TEAM:**  
   * Quyền truy cập vào CKG (thông qua CKGQueryInterfaceAgent).  
   * TaskDefinition từ Orchestrator (chỉ định loại phân tích cần thực hiện, phạm vi, cấu hình linter nếu có).  
   * Đường dẫn đến mã nguồn (để chạy linter).  
4. **Output chính của TEAM:**  
   * Một tập hợp các "Phát hiện Phân tích" (Analysis Findings) được cấu trúc, bao gồm:  
     * Mô tả vấn đề.  
     * Mức độ nghiêm trọng (gợi ý).  
     * Vị trí trong code (file, dòng).  
     * (Có thể) Gợi ý sửa lỗi hoặc cải thiện.  
   * Dữ liệu ngữ cảnh đã được chuẩn bị cho các yêu cầu gửi đến TEAM LLM Services.  
5. **Thành viên Agent trong TEAM:**  
   * **ArchitecturalAnalyzerAgent (Agent Phân tích Kiến trúc)**  
     * **Mục tiêu:** Phát hiện các vấn đề và rủi ro liên quan đến kiến trúc phần mềm.  
     * **Trách nhiệm (v1.0):**  
       * Truy vấn CKG để xây dựng đồ thị phụ thuộc giữa các file/module.  
       * Áp dụng thuật toán phát hiện chu trình (cycle detection) để tìm circular dependencies.  
       * Truy vấn CKG để tìm các public entities không có lời gọi đến từ bên ngoài module của chúng (trong phạm vi codebase).  
     * **Input:** Quyền truy cập CKG, các quy tắc/heuristic về kiến trúc (ban đầu có thể là hard-coded).  
     * **Output:** Danh sách các vấn đề kiến trúc đã phát hiện.  
   * **StaticAnalysisIntegratorAgent (Agent Tích hợp Phân tích Tĩnh)**  
     * **Mục tiêu:** Tận dụng sức mạnh của các công cụ linter/static analyzer hiện có và tích hợp kết quả của chúng một cách nhất quán.  
     * **Trách nhiệm:**  
       * Dựa trên ngôn ngữ của project, kích hoạt các linter/analyzer phù hợp.  
       * Thu thập output từ các công cụ này (thường là JSON hoặc XML).  
       * Chuẩn hóa output thành một định dạng "Finding" chung của AI CodeScan.  
     * **Input:** Đường dẫn mã nguồn, cấu hình linter (nếu có).  
     * **Output:** Danh sách các "Finding" đã được chuẩn hóa từ các công cụ linter.  
     * **Công nghệ đề xuất:**  
       * Java: Checkstyle, PMD.  
       * Kotlin: Detekt, Ktlint.  
       * Dart: Dart Analyzer.  
       * Python: Flake8, Pylint.  
   * **ContextualQueryAgent (Agent Truy vấn Ngữ cảnh CKG)**  
     * **Mục tiêu:** Tạo ra các truy vấn CKG thông minh và hiệu quả để thu thập ngữ cảnh cần thiết cho các agent phân tích khác hoặc cho việc chuẩn bị dữ liệu gửi LLM.  
     * **Trách nhiệm:**  
       * Dựa trên mục tiêu phân tích hoặc câu hỏi cụ thể, xây dựng các truy vấn Cypher (hoặc sử dụng API của CKGQueryInterfaceAgent) để lấy thông tin liên quan.  
     * **Input:** Mục tiêu phân tích.  
     * **Output:** Kết quả truy vấn CKG dưới dạng cấu trúc dữ liệu.  
   * **LLMAnalysisSupportAgent (Agent Hỗ trợ Phân tích bằng LLM)**  
     * **Mục tiêu:** Chuẩn bị dữ liệu và tạo yêu cầu để TEAM LLM Services có thể thực hiện các phân tích hoặc trả lời câu hỏi dựa trên LLM.  
     * **Trách nhiệm:**  
       * Tập hợp các đoạn code liên quan (từ mã nguồn) và thông tin ngữ cảnh (từ kết quả của ContextualQueryAgent hoặc CKG).  
       * Định dạng dữ liệu này và tạo một yêu cầu rõ ràng (bao gồm câu hỏi hoặc loại phân tích mong muốn) để gửi đến TEAM LLM Services.  
     * **Input:** Đoạn code cần phân tích, thông tin ngữ cảnh từ CKG, câu hỏi/yêu cầu phân tích cụ thể.  
     * **Output:** Một "LLMServiceRequest" object/structure gửi đến TEAM LLM Services.  
6. **Công cụ (Tools) / Giao thức Đa Ngữ cảnh (MCPs) cần phát triển cho TEAM:**  
   * **CKG Query API Client:** Để tương tác với CKGQueryInterfaceAgent.  
   * **Linter Execution Framework:** Một framework để dễ dàng gọi và quản lý việc thực thi các linter/analyzer khác nhau cho các ngôn ngữ.  
   * **Standardized Finding Format (SFF):** Một MCP (ví dụ: JSON Schema) định nghĩa cấu trúc chung cho tất cả các "Phát hiện Phân tích".  
   * **LLMServiceRequest Protocol:** MCP định nghĩa định dạng yêu cầu gửi đến TEAM LLM Services.  
   * **Thư viện phân tích đồ thị:** (Có thể dùng NetworkX nếu cần xử lý các đồ thị con cục bộ trước khi truy vấn CKG lớn).  
7. **Cơ chế Phối hợp:**  
   * Nhận yêu cầu phân tích từ Orchestrator.  
   * Các agent trong TEAM hoạt động song song hoặc tuần tự tùy thuộc vào loại phân tích.  
   * ContextualQueryAgent hỗ trợ các agent khác bằng cách cung cấp dữ liệu từ CKG.  
   * LLMAnalysisSupportAgent gửi yêu cầu đến TEAM LLM Services khi cần sự can thiệp của LLM.  
   * Tất cả các "Finding" được thu thập và gửi cho TEAM Synthesis & Reporting.  
8. **Chủ đề Nghiên cứu Chuyên sâu (Gemini Deep Research Topics):**  
   * **Phát hiện Anti-Pattern Kiến trúc Nâng cao và Đa Ngôn ngữ:** Phát triển các thuật toán và mô hình để phát hiện các anti-pattern kiến trúc phức tạp.  
   * **Phân tích Luồng Dữ liệu (Data Flow Analysis) trên CKG:** Nghiên cứu cách biểu diễn và phân tích luồng dữ liệu trong CKG.  
   * **Đánh giá Rủi ro Thay đổi và Phân tích Tác động PR Sâu sắc:** Các kỹ thuật để dự đoán rủi ro của một PR.  
   * **Tự động Gợi ý Refactoring Thông minh:** Hệ thống có thể gợi ý các giải pháp refactoring cụ thể không?  
   * **Đo lường và Cải thiện "Code Quality" một cách Toàn diện:** Đánh giá các khía cạnh trừu tượng hơn của chất lượng code.

### **F. TEAM LLM Services (Đội Dịch vụ LLM)**

1. Mục tiêu chung của TEAM:  
   Đóng vai trò là một trung tâm dịch vụ chuyên biệt và được tối ưu hóa cho tất cả các tương tác với Mô hình Ngôn ngữ Lớn (LLM). Đảm bảo việc sử dụng LLM trong AI CodeScan là hiệu quả, nhất quán, dễ quản lý và có khả năng mở rộng sang các nhà cung cấp LLM khác nhau trong tương lai.  
2. **Trách nhiệm chính của TEAM:**  
   * Tiếp nhận các yêu cầu sử dụng LLM từ các TEAM khác.  
   * Quản lý **Lớp Trừu tượng LLM (LLM Abstraction Layer)**: Cung cấp một interface (API) nội bộ nhất quán.  
   * **Quản lý và Tối ưu hóa Prompt (Prompt Engineering & Management):** Xây dựng, lưu trữ, phiên bản hóa và tối ưu hóa các prompt.  
   * **Quản lý Ngữ cảnh (Context Management):** Nhận ngữ cảnh, xử lý và định dạng ngữ cảnh.  
   * Thực thi các lời gọi đến API của LLM (ví dụ: OpenAI API cho v1.0).  
   * Xử lý các phản hồi từ LLM.  
   * Trả kết quả đã xử lý về cho TEAM đã yêu cầu.  
3. **Input chính của TEAM:**  
   * LLMServiceRequest object/structure từ các TEAM khác.  
4. **Output chính của TEAM:**  
   * LLMServiceResponse object/structure.  
5. **Thành viên Agent trong TEAM (Hoặc các Module/Component chuyên biệt):**  
   * **LLMGatewayAgent (Agent Cổng kết nối LLM)**  
     * **Mục tiêu:** Là điểm vào duy nhất cho tất cả các yêu cầu tương tác với LLM.  
     * **Trách nhiệm:** Tiếp nhận LLMServiceRequest, phối hợp chuẩn bị input, gọi LLM provider, nhận phản hồi, đóng gói LLMServiceResponse.  
     * **Công nghệ đề xuất:** OpenAI API client.  
   * **PromptFormatterModule (Module Định dạng và Quản lý Prompt)**  
     * **Mục tiêu:** Cung cấp các prompt đã được thiết kế và tối ưu hóa.  
     * **Trách nhiệm:** Lưu trữ thư viện prompt template, chọn template, điền ngữ cảnh.  
   * **ContextProviderModule (Module Xử lý và Cung cấp Ngữ cảnh)**  
     * **Mục tiêu:** Chuẩn bị và tối ưu hóa ngữ cảnh cho LLM.  
     * **Trách nhiệm:** Nhận ngữ cảnh, chọn lọc, tóm tắt, cắt tỉa, định dạng.  
   * **LLMProviderAbstractionLayer (Lớp Trừu tượng Nhà cung cấp LLM)**  
     * **Mục tiêu:** Cho phép dễ dàng chuyển đổi giữa các nhà cung cấp LLM.  
     * **Trách nhiệm:** Định nghĩa interface chung, các implementation cụ thể (ví dụ: OpenAIProvider).  
6. **Công** cụ (Tools) / Giao thức Đa Ngữ cảnh (MCPs) cần **phát triển cho TEAM:**  
   * **LLMServiceRequest/Response Protocol (LSRP):** MCP định nghĩa cấu trúc chuẩn.  
   * **Prompt Template Library/Management System:** Hệ thống lưu trữ, phiên bản hóa prompt.  
   * **Contextualization Engine Rules:** Quy tắc và thuật toán xử lý ngữ cảnh.  
   * **API Clients for LLM Providers:** (Ví dụ: thư viện openai cho Python).  
   * **LLM Abstraction Interface Definition.**  
7. **Cơ chế Phối hợp:**  
   * Hoạt động như một TEAM dịch vụ. Nhận LLMServiceRequest, xử lý, trả LLMServiceResponse.  
8. **Chủ đề Nghiên cứu Chuyên sâu (Gemini Deep Research Topics):**  
   * **Thiết kế Tối ưu và Linh hoạt cho LLM Abstraction Layer:** Nghiên cứu design pattern và kiến trúc.  
   * **Advanced Retrieval Augmented Generation (RAG) for Code Understanding:** Phát triển kiến trúc RAG tiên tiến.  
   * **Robust Prompt Engineering Framework for Code-Specific Tasks:** Xây dựng bộ khung thiết kế prompt.  
   * **Strategies for Evaluating, Monitoring, and Mitigating LLM Hallucinations in Code Context:** Phát triển phương pháp phát hiện "ảo giác".  
   * **Cost-Performance Optimization for LLM Usage:** Nghiên cứu chiến lược tối ưu chi phí.  
   * **Feasibility** and Roadmap for Fine-tuning/Specializing **LLMs for AI CodeScan:** Đánh giá khả năng fine-tuning LLM.

### **G. TEAM Synthesis & Reporting (Đội Tổng hợp & Báo cáo)**

1. Mục tiêu chung của TEAM:  
   Tổng hợp một cách thông minh tất cả các phát hiện, phân tích từ các TEAM khác, tạo ra các báo cáo review code cuối cùng rõ ràng, dễ hiểu, có tính hành động cao, và hỗ trợ người dùng tương tác với kết quả thông qua việc sinh sơ đồ hoặc các hình thức trực quan hóa khác.  
2. **Trách nhiệm chính của TEAM (v1.0):**  
   * Thu thập và hợp nhất các "Phát hiện Phân tích" từ TEAM Code Analysis.  
   * Tiếp nhận các kết quả phân tích hoặc nội dung từ TEAM LLM Services.  
   * Sử dụng LLM để tóm tắt các phát hiện quan trọng.  
   * Tạo ra báo cáo review code cuối cùng (text, markdown, JSON).  
   * **Sinh Sơ đồ Lớp (Class Diagram):** Sinh mã PlantUML/Mermaid.js.  
   * **Tạo Tóm tắt Tác động PR:** Tổng hợp và trình bày súc tích.  
   * Định dạng toàn bộ output để TEAM Interaction & Tasking hiển thị.  
3. **Input chính của TEAM:**  
   * Tập hợp các AnalysisFinding object/structure.  
   * Các LLMServiceResponse object/structure.  
   * Yêu cầu sinh sơ đồ hoặc loại báo cáo cụ thể.  
   * Quyền truy cập CKG.  
4. **Output chính của TEAM:**  
   * FinalReviewReport object/structure.  
   * Mã nguồn cho sơ đồ (PlantUML/Mermaid.js text).  
   * Các câu trả lời Q\&A đã được tổng hợp và định dạng.  
   * Toàn bộ output được đóng gói để hiển thị.  
5. **Thành viên Agent trong TEAM:**  
   * **FindingAggregatorAgent (Agent Tổng hợp và Ưu tiên Phát hiện)**  
     * **Mục tiêu:** Hợp nhất và xử lý thông minh các phát hiện.  
     * **Trách nhiệm:** Thu thập, loại bỏ trùng lặp, ưu tiên, nhóm phát hiện.  
   * **ReportGeneratorAgent (Agent Tạo Báo cáo Tường thuật)**  
     * **Mục tiêu:** Tạo báo cáo review code dễ đọc, dễ hiểu.  
     * **Trách nhiệm:** Sử dụng phát hiện, yêu cầu TEAM LLM Services sinh tóm tắt/giải thích, kết hợp thành báo cáo.  
   * **DiagramGeneratorAgent (Agent Sinh Sơ đồ)**  
     * **Mục tiêu:** Tạo mã nguồn cho sơ đồ kiến trúc.  
     * **Trách nhiệm (v1.0 \- Class Diagram):** Nhận yêu cầu, truy vấn CKG, chuyển đổi thông tin thành PlantUML/Mermaid.js.  
     * **Công nghệ đề xuất:** Thư viện sinh mã PlantUML/Mermaid.js.  
   * **OutputFormatterAgent (Agent Định dạng Output Cuối cùng)**  
     * **Mục tiêu:** Đảm bảo thông tin trình bày nhất quán, phù hợp.  
     * **Trách nhiệm:** Tập hợp báo cáo, mã sơ đồ, đóng gói.  
6. **Công cụ (Tools) / Giao thức Đa Ngữ cảnh (MCPs) cần phát triển cho TEAM:**  
   * **FinalReviewReport Schema:** MCP định nghĩa cấu trúc báo cáo cuối cùng.  
   * **DiagramData Protocol:** MCP định nghĩa cách truyền tải yêu cầu và kết quả sinh sơ đồ.  
   * **Thư viện Sinh mã PlantUML/Mermaid.js.**  
   * **Template Engine (nếu cần):** Để tạo báo cáo có cấu trúc.  
7. **Cơ chế Phối hợp:**  
   * Nhận dữ liệu phân tích và yêu cầu đặc biệt từ Orchestrator.  
   * Các agent nội bộ xử lý, tạo output cuối cùng, có thể yêu cầu TEAM LLM Services.  
   * OutputFormatterAgent đóng gói và gửi cho Orchestrator để hiển thị.  
8. **Chủ đề Nghiên cứu Chuyên sâu (Gemini Deep Research Topics):**  
   * **Tự động Tạo Báo cáo Review Code Thông minh và Có Tính Thuyết phục Cao:** Nghiên cứu cách LLM viết báo cáo chuyên nghiệp.  
   * **Trực quan hóa Dữ liệu Phân tích Code Nâng cao và Tương tác:** Sinh sơ đồ phức tạp hơn, tương tác với sơ đồ.  
   * **Cá nhân hóa Báo cáo và Gợi ý:** Tùy chỉnh báo cáo theo vai trò, kinh nghiệm người dùng.  
   * **Đo lường và Cải thiện Tính "Hành động được" (Actionability) của Báo cáo:** Phát triển metrics đánh giá.  
   * **Tích hợp Phản hồi Người dùng vào Chu trình Cải thiện Báo cáo:** Thiết kế cơ chế thu thập phản hồi.

## **Phần IV: Công nghệ và Công cụ Đề xuất cho v1.0**

Dưới đây là tổng hợp các công nghệ và công cụ chính được đề xuất cho việc triển khai AI CodeScan v1.0:

* **Ngôn ngữ phát triển chính:** Python.  
* **Giao** diện người **dùng (UI):**  
  * Ban đầu: Giao diện dòng lệnh (CLI) \- ví dụ: thư viện click trong Python.  
  * Giao diện web đơn giản: Streamlit.  
* **Mô hình Ngôn ngữ Lớn (LLM):**  
  * API của OpenAI (ví dụ: các model GPT).  
  * Thư viện client: openai (Python).  
* **Code Knowledge Graph (CKG):**  
  * Graph Database: Neo4j Community Edition.  
  * Ngôn ngữ truy vấn: Cypher.  
  * Thư viện client: neo4j (Python).  
* **Parsers mã nguồn:**  
  * Java: Thư viện javaparser (Java, cần tích hợp vào Python qua JEP \- Java Embedded Python, hoặc chạy process riêng).  
  * Kotlin: Khai thác Kotlin Compiler API hoặc Detekt (Kotlin, tương tự Java cần cơ chế tích hợp).  
  * Dart: analyzer package từ Dart SDK (Dart, cần cơ chế tích hợp).  
  * Python: Module ast (tích hợp sẵn trong Python).  
* **Linters / Static Analyzers (Tích hợp):**  
  * Java: Checkstyle, PMD.  
  * Kotlin: Detekt, Ktlint.  
  * Dart: Dart Analyzer.  
  * Python: Flake8, Pylint.  
* **Thao** tác **Git:**  
  * Thư viện gitpython (Python).  
* **Tương tác API** Git **Platform (ví dụ: GitHub):**  
  * Thư viện PyGithub (Python).  
* **Xử lý Ngôn ngữ Tự nhiên (NLU) (cho UserIntentParserAgent):**  
  * Thư viện spaCy (Python).  
  * Thư viện RASA NLU (Python).  
  * Hoặc sử dụng khả năng NLU của API LLM (OpenAI).  
* **Định danh Ngôn ngữ Lập trình:**  
  * Thư viện python-linguist (Python, dựa trên Linguist của GitHub).  
  * Hoặc phát triển heuristics tùy chỉnh.  
* **Agent Framework / Orchestration:**  
  * Xem xét LangGraph (Python) cho WorkflowEngineModule trong Orchestrator.  
* **Sinh sơ đồ:**  
  * PlantUML (cần cài đặt PlantUML và Graphviz).  
  * Mermaid.js (sinh mã text, render phía client nếu là web UI).  
  * Thư viện Python để sinh mã PlantUML/Mermaid.js.  
* **Quản lý Session / Bộ nhớ tạm thời:**  
  * Xem xét các giải pháp như Mem0 hoặc các thư viện caching đơn giản trong Python.

Việc lựa chọn công nghệ cụ thể cho từng thành phần sẽ cần được đánh giá kỹ lưỡng hơn trong quá trình triển khai, dựa trên các yếu tố như hiệu năng, tính dễ tích hợp, sự hỗ trợ của cộng đồng và chi phí (nếu có). Ưu tiên hàng đầu là sử dụng các công cụ mã nguồn mở và các thư viện Python phổ biến để thuận tiện cho việc phát triển và bảo trì.