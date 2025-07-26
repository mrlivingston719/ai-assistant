#!/bin/bash

# RovoDev Phase 1 Week 1 Validation Script
# Tests foundation infrastructure and core services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}Testing:${NC} $1"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

print_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

print_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

print_info() {
    echo -e "${BLUE}ℹ️  INFO:${NC} $1"
}

# Test function wrapper
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    print_test "$test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        print_pass "$test_name"
        return 0
    else
        print_fail "$test_name"
        return 1
    fi
}

# Test function with output capture
run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    
    print_test "$test_name"
    
    local output
    output=$(eval "$test_command" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_pass "$test_name"
        if [ -n "$3" ]; then
            echo -e "   ${BLUE}→${NC} $output"
        fi
        return 0
    else
        print_fail "$test_name"
        echo -e "   ${RED}→${NC} $output"
        return 1
    fi
}

# Main validation function
main() {
    print_header "RovoDev Phase 1 Week 1 Validation"
    
    echo "Validating foundation infrastructure and core services..."
    echo "Date: $(date)"
    echo "Host: $(hostname)"
    echo ""
    
    # ========================================
    # 1. DOCKER INFRASTRUCTURE
    # ========================================
    print_header "1. Docker Infrastructure"
    
    run_test "Docker is running" "docker --version"
    run_test "Docker Compose is available" "docker compose version"
    
    # Check if containers exist
    print_test "Checking container status"
    if docker compose ps >/dev/null 2>&1; then
        print_pass "Docker Compose project found"
        
        # Get container status
        local containers_status
        containers_status=$(docker compose ps --format "table {{.Name}}\t{{.Status}}")
        echo -e "   ${BLUE}→${NC} Container Status:"
        echo "$containers_status" | tail -n +2 | while read -r line; do
            echo -e "     ${BLUE}•${NC} $line"
        done
    else
        print_fail "Docker Compose project not found or not running"
    fi
    
    # Check individual containers
    run_test "PostgreSQL container healthy" "docker compose ps postgres | grep -q 'healthy'"
    run_test "ChromaDB container healthy" "docker compose ps chromadb | grep -q 'healthy'"
    run_test "Assistant container running" "docker compose ps assistant | grep -q 'Up'"
    
    # ========================================
    # 2. NETWORK CONNECTIVITY
    # ========================================
    print_header "2. Network Connectivity"
    
    run_test "Port 8080 is bound (FastAPI)" "netstat -tlnp | grep -q ':8080'"
    run_test "Port 5432 is bound (PostgreSQL)" "netstat -tlnp | grep -q ':5432'"
    run_test "Port 8000 is bound (ChromaDB)" "netstat -tlnp | grep -q ':8000'"
    run_test "Port 11434 is accessible (Ollama)" "netstat -tlnp | grep -q ':11434' || curl -s http://localhost:11434/api/tags >/dev/null"
    
    # ========================================
    # 3. SERVICE HEALTH CHECKS
    # ========================================
    print_header "3. Service Health Checks"
    
    # FastAPI Health
    print_test "FastAPI health endpoint"
    if curl -s -f http://localhost:8080/health >/dev/null 2>&1; then
        print_pass "FastAPI health endpoint responding"
        local health_response
        health_response=$(curl -s http://localhost:8080/health | jq -r '.status' 2>/dev/null || echo "unknown")
        print_info "Health status: $health_response"
    else
        print_fail "FastAPI health endpoint not responding"
        print_info "Check: docker compose logs assistant"
    fi
    
    # FastAPI Status
    run_test_with_output "FastAPI status endpoint" "curl -s -f http://localhost:8080/status" "show"
    
    # PostgreSQL Connection
    print_test "PostgreSQL connection"
    if docker exec assistant-postgres psql -U assistant -d assistant -c "SELECT 1;" >/dev/null 2>&1; then
        print_pass "PostgreSQL connection working"
        local db_info
        db_info=$(docker exec assistant-postgres psql -U assistant -d assistant -c "SELECT version();" -t 2>/dev/null | head -1 | xargs)
        print_info "Database: $db_info"
    else
        print_fail "PostgreSQL connection failed"
    fi
    
    # ChromaDB Health
    print_test "ChromaDB health"
    if curl -s -f http://localhost:8000/api/v1/version >/dev/null 2>&1; then
        print_pass "ChromaDB responding"
        local chroma_version
        chroma_version=$(curl -s http://localhost:8000/api/v1/version 2>/dev/null || echo "unknown")
        print_info "ChromaDB version: $chroma_version"
    else
        print_fail "ChromaDB not responding"
    fi
    
    # Ollama Health
    print_test "Ollama service"
    if command -v ollama >/dev/null 2>&1; then
        if curl -s -f http://localhost:11434/api/tags >/dev/null 2>&1; then
            print_pass "Ollama service responding"
            local model_count
            model_count=$(curl -s http://localhost:11434/api/tags 2>/dev/null | jq '.models | length' 2>/dev/null || echo "0")
            print_info "Available models: $model_count"
        else
            print_fail "Ollama installed but not responding"
            print_info "Try: systemctl start ollama"
        fi
    else
        print_fail "Ollama not installed (required for Phase 1 Week 1)"
        print_info "Install with: curl -fsSL https://ollama.ai/install.sh | sh"
    fi
    
    # ========================================
    # 4. CONFIGURATION VALIDATION
    # ========================================
    print_header "4. Configuration Validation"
    
    run_test "Environment file exists" "test -f .env"
    
    if [ -f .env ]; then
        # Check critical environment variables
        print_test "PostgreSQL password configured"
        if grep -q "POSTGRES_PASSWORD=" .env && ! grep -q "POSTGRES_PASSWORD=your_secure_postgres_password" .env; then
            print_pass "PostgreSQL password is configured"
        else
            print_fail "PostgreSQL password not configured or using default"
        fi
        
        print_test "Signal phone number configured"
        if grep -q "SIGNAL_PHONE_NUMBER=" .env && ! grep -q "SIGNAL_PHONE_NUMBER=your_signal_number" .env; then
            print_pass "Signal phone number is configured"
        else
            print_fail "Signal phone number not configured or using default"
        fi
    fi
    
    # ========================================
    # 5. BASIC FUNCTIONALITY TESTS
    # ========================================
    print_header "5. Basic Functionality Tests"
    
    # Test database table creation
    print_test "Database tables exist"
    if docker exec assistant-postgres psql -U assistant -d assistant -c "\dt" 2>/dev/null | grep -q "users\|meetings"; then
        print_pass "Database tables created"
        local table_count
        table_count=$(docker exec assistant-postgres psql -U assistant -d assistant -c "\dt" 2>/dev/null | grep -c "public |" || echo "0")
        print_info "Tables found: $table_count"
    else
        print_fail "Database tables not found"
        print_info "Tables may not be initialized yet"
    fi
    
    # Test Ollama model availability
    if command -v ollama >/dev/null 2>&1; then
        print_test "Qwen2.5-14B model available"
        if ollama list 2>/dev/null | grep -q "qwen2.5:14b"; then
            print_pass "Qwen2.5-14B model is available"
            
            # Test basic model response
            print_test "Ollama model response test"
            if timeout 30 ollama run qwen2.5:14b "Hello" >/dev/null 2>&1; then
                print_pass "Ollama model responding"
            else
                print_fail "Ollama model not responding or timeout"
            fi
        else
            print_fail "Qwen2.5-14B model not found (required for Phase 1 Week 1)"
            print_info "Download with: ollama pull qwen2.5:14b"
        fi
    else
        print_fail "Ollama not installed - cannot test model"
        print_info "Install Ollama first, then download model"
    fi
    
    # ========================================
    # 6. RESOURCE USAGE
    # ========================================
    print_header "6. System Resources"
    
    # Memory usage
    local total_mem
    total_mem=$(free -g | awk '/^Mem:/{print $2}')
    local used_mem
    used_mem=$(free -g | awk '/^Mem:/{print $3}')
    print_info "Memory: ${used_mem}GB used / ${total_mem}GB total"
    
    # Disk usage
    local disk_usage
    disk_usage=$(df -h . | awk 'NR==2{print $5}')
    print_info "Disk usage: $disk_usage"
    
    # Docker resource usage
    print_info "Docker container resource usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | tail -n +2 | while read -r line; do
        echo -e "     ${BLUE}•${NC} $line"
    done
    
    # ========================================
    # SUMMARY
    # ========================================
    print_header "Validation Summary"
    
    echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    
    local success_rate
    success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "Success Rate: ${BLUE}${success_rate}%${NC}"
    
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
        echo -e "${GREEN}Phase 1 Week 1 foundation is ready!${NC}"
        echo ""
        echo -e "${BLUE}Next Steps:${NC}"
        echo "1. Configure Signal phone number in .env"
        echo "2. Test Signal integration functionality"
        echo "3. Begin Phase 1 Week 2 development"
        exit 0
    elif [ $success_rate -ge 80 ]; then
        echo -e "${YELLOW}⚠️  MOSTLY READY${NC}"
        echo -e "${YELLOW}Foundation is mostly working with minor issues${NC}"
        echo ""
        echo -e "${BLUE}Issues to address:${NC}"
        echo "• Review failed tests above"
        echo "• Check logs: docker compose logs"
        echo "• Verify configuration in .env"
        exit 1
    else
        echo -e "${RED}❌ SIGNIFICANT ISSUES FOUND${NC}"
        echo -e "${RED}Foundation needs attention before proceeding${NC}"
        echo ""
        echo -e "${BLUE}Troubleshooting:${NC}"
        echo "• Check container logs: docker compose logs"
        echo "• Verify all services are running: docker compose ps"
        echo "• Check system resources: free -h && df -h"
        echo "• Review configuration: cat .env"
        exit 2
    fi
}

# Run main function
main "$@"