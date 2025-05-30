#!/usr/bin/env python3
"""
Test LangGraph Integration - AI CodeScan

Script này test LangGraph workflow với project review example.
"""

import sys
import os
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.orchestrator.project_review_graph import create_project_review_graph
from core.orchestrator.base_graph import Repository, TaskType, TaskStatus
from loguru import logger

def setup_logging():
    """Setup logging cho test."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/test_langgraph_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )

def test_project_review_workflow():
    """
    Test complete project review workflow với LangGraph.
    """
    logger.info("🚀 Bắt đầu test LangGraph Project Review Workflow")
    
    try:
        # 1. Tạo graph instance
        logger.info("📊 Tạo ProjectReviewGraph instance...")
        graph = create_project_review_graph()
        
        # 2. Compile graph
        logger.info("⚙️ Compile graph...")
        compiled_graph = graph.compile_graph()
        
        # 3. Tạo test repository info
        test_repo = Repository(
            url="https://github.com/example/test-repo",
            branch="main",
            commit_hash="abc123def456"
        )
        
        # 4. Tạo initial state
        task_id = str(uuid.uuid4())
        logger.info(f"📝 Tạo initial state với task_id: {task_id}")
        
        initial_state = graph.create_initial_state(
            task_id=task_id,
            task_type=TaskType.PROJECT_REVIEW,
            repository=test_repo,
            metadata={
                "test_mode": True,
                "created_by": "test_script"
            }
        )
        
        # 5. Execute workflow
        logger.info("🔄 Bắt đầu execute workflow...")
        logger.info("=" * 60)
        
        final_state = graph.execute(initial_state)
        
        logger.info("=" * 60)
        logger.info("✅ Workflow hoàn thành!")
        
        # 6. Hiển thị kết quả
        display_results(final_state)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test thất bại: {str(e)}")
        return False

def test_streaming_execution():
    """
    Test streaming execution của LangGraph workflow.
    """
    logger.info("🌊 Bắt đầu test Streaming Execution")
    
    try:
        # Tạo graph
        graph = create_project_review_graph()
        
        # Tạo test data
        test_repo = Repository(
            url="https://github.com/example/streaming-test",
            branch="develop"
        )
        
        task_id = str(uuid.uuid4())
        initial_state = graph.create_initial_state(
            task_id=task_id,
            task_type=TaskType.PROJECT_REVIEW,
            repository=test_repo
        )
        
        # Stream execution
        logger.info("📡 Bắt đầu streaming execution...")
        
        for i, chunk in enumerate(graph.stream_execute(initial_state)):
            if "error" in chunk:
                logger.error(f"Stream chunk {i}: Error - {chunk['error']}")
                break
            else:
                logger.info(f"Stream chunk {i}: {list(chunk.keys())}")
        
        logger.info("✅ Streaming test hoàn thành!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Streaming test thất bại: {str(e)}")
        return False

def test_state_management():
    """
    Test state management và checkpointing.
    """
    logger.info("💾 Bắt đầu test State Management")
    
    try:
        graph = create_project_review_graph()
        
        # Test save/load state
        test_repo = Repository(url="https://github.com/example/state-test")
        task_id = str(uuid.uuid4())
        
        initial_state = graph.create_initial_state(
            task_id=task_id,
            task_type=TaskType.PROJECT_REVIEW,
            repository=test_repo
        )
        
        # Execute một phần workflow
        logger.info("🔄 Execute workflow...")
        final_state = graph.execute(initial_state)
        
        # Test get state
        logger.info("📖 Test get state...")
        retrieved_state = graph.get_state(task_id)
        
        if retrieved_state:
            logger.info(f"✅ State retrieved successfully: {retrieved_state.get('status')}")
        else:
            logger.warning("⚠️ Could not retrieve state")
        
        # Test state history
        logger.info("📚 Test state history...")
        history = graph.get_state_history(task_id, limit=5)
        logger.info(f"📊 Found {len(history)} state snapshots")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ State management test thất bại: {str(e)}")
        return False

def display_results(final_state):
    """
    Hiển thị kết quả workflow.
    
    Args:
        final_state: Final state sau khi execute
    """
    logger.info("📋 KQUÁ QUẢ WORKFLOW")
    logger.info("=" * 50)
    
    # Basic info
    logger.info(f"Task ID: {final_state.get('task_id')}")
    logger.info(f"Status: {final_state.get('status')}")
    logger.info(f"Task Type: {final_state.get('task_type')}")
    
    # Repository info
    repo = final_state.get("repository")
    if repo:
        logger.info(f"Repository: {repo.url}")
        logger.info(f"Branch: {repo.branch}")
    
    # Metadata
    metadata = final_state.get("metadata", {})
    logger.info(f"Total Files: {metadata.get('total_files', 'N/A')}")
    logger.info(f"Languages: {metadata.get('languages_detected', [])}")
    logger.info(f"Project Size: {metadata.get('project_size', 'N/A')} bytes")
    
    # Analysis results
    analysis_results = final_state.get("analysis_results", {})
    
    # Code analysis
    code_analysis = analysis_results.get("code_analysis", {})
    if code_analysis:
        quality = code_analysis.get("code_quality", {})
        logger.info(f"Overall Score: {quality.get('overall_score', 'N/A')}/10")
        logger.info(f"Test Coverage: {quality.get('test_coverage', 'N/A')}%")
    
    # LLM insights
    llm_insights = analysis_results.get("llm_insights", {})
    if llm_insights:
        logger.info(f"Executive Summary: {llm_insights.get('executive_summary', 'N/A')}")
        
        recommendations = llm_insights.get("recommendations", [])
        if recommendations:
            logger.info(f"Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"  {i}. [{rec.get('priority')}] {rec.get('title')}")
                logger.info(f"     {rec.get('description')}")
    
    # Knowledge Graph
    kg = final_state.get("knowledge_graph", {})
    if kg:
        metrics = kg.get("metrics", {})
        logger.info(f"Knowledge Graph: {metrics.get('total_entities', 0)} entities, {metrics.get('total_relationships', 0)} relationships")
    
    # Errors
    errors = final_state.get("errors", [])
    if errors:
        logger.error(f"Errors ({len(errors)}):")
        for error in errors:
            logger.error(f"  - {error}")
    
    # Responses
    responses = final_state.get("responses", [])
    if responses:
        logger.info(f"System Responses:")
        for response in responses:
            logger.info(f"  💬 {response}")

def main():
    """Main test function."""
    setup_logging()
    
    logger.info("🧪 AI CodeScan - LangGraph Integration Test")
    logger.info("=" * 60)
    
    # Tạo logs directory
    os.makedirs("logs", exist_ok=True)
    
    test_results = []
    
    # Test 1: Basic workflow
    logger.info("\n🧪 TEST 1: Basic Project Review Workflow")
    logger.info("-" * 40)
    test_results.append(("Basic Workflow", test_project_review_workflow()))
    
    # Test 2: Streaming execution
    logger.info("\n🧪 TEST 2: Streaming Execution")
    logger.info("-" * 40)
    test_results.append(("Streaming Execution", test_streaming_execution()))
    
    # Test 3: State management
    logger.info("\n🧪 TEST 3: State Management")
    logger.info("-" * 40)
    test_results.append(("State Management", test_state_management()))
    
    # Summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nKết quả: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        logger.info("🎉 Tất cả tests đều PASS! LangGraph integration hoạt động tốt.")
    else:
        logger.warning("⚠️ Một số tests FAIL. Cần kiểm tra và fix.")
    
    return passed == len(test_results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 