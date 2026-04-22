#!/bin/bash
# Fake Jack Vanleur — Test Agent
# Simulates a real estate agent using JackConnect
# Run: bash test-fake-agent.sh

JOBS=(
  "seo-audit|Test Agent|testagent@fakejack.com|https://fakehouse123.com|The siding color is wrong on listing|"
  "lead-gen|Fake Jack|jack@fakerealestate.com|https://fakejackhomes.com|Needs leads in zip 55406|3 day turnaround"
  "cold-email|Fake Agent|fakeagent@realestate.com|https://fakepropertylistings.com|Send to agent leads in Edina|"
  "cma-report|Property Tester|prop@test.com|https://fakeproperty123.com|CMA for 7421 York Ave S|24 hour"
)

PORTAL="https://josephv.zo.space"

echo "🏠 JackConnect Fake Agent — Starting"
echo "======================================"

for job in "${JOBS[@]}"; do
  IFS='|' read -r type name email url notes <<< "$job"
  echo ""
  echo "📤 Submitting: $name — $type"
  
  result=$(curl -s -X POST "$PORTAL/api/jackconnect/submit-job" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\",\"email\":\"$email\",\"jobType\":\"$type\",\"url\":\"$url\",\"notes\":\"$notes\"}")
  
  echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'  Job ID: {d.get(\"jobId\",\"N/A\")}'); print(f'  Price: \${d.get(\"price\",0)}'); print(f'  Status: {d.get(\"status\",\"N/A\")}')" 2>/dev/null || echo "$result"
  
  sleep 2
done

echo ""
echo "======================================"
echo "✅ All test jobs submitted"
echo "Check: https://josephv.zo.space/jackconnect/worker"
