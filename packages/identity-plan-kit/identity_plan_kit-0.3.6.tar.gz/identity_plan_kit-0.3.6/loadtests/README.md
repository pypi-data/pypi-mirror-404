# Load Testing for identity-plan-kit

Comprehensive Locust-based load tests for validating identity-plan-kit under high concurrency and load.

# Install load test dependencies
uv pip install "identity-plan-kit[loadtest]"       
# Start your application
uvicorn your_app:app --host 0.0.0.0 --port 8000

# Run load tests with web UI
cd loadtests
locust -f locustfile.py

# Open http://localhost:8089 in your browser
```

## Test Modules

### 1. `test_auth.py` - Authentication Load Tests
Tests authentication endpoints under load:
- **Token refresh** - Concurrent token rotation
- **Logout operations** - Single and "everywhere" logout
- **User info** - `/me` and `/profile` endpoints
- **Concurrent refresh** - Race condition testing

```bash
locust -f loadtests/test_auth.py --headless -u 50 -r 5 -t 2m
```

### 2. `test_rbac_cache.py` - Permission Cache Tests
Tests the RBAC permission cache:
- **Cache hit ratio** - Measures cache effectiveness
- **Cache warming** - Cold start performance
- **Concurrent access** - Same user, multiple requests
- **Mixed workloads** - Reads with occasional invalidation

```bash
locust -f loadtests/test_rbac_cache.py --headless -u 100 -r 10 -t 3m
```

### 3. `test_plans_quota.py` - Plans & Quota Tests
Tests subscription and quota system:
- **Plan info loading** - Performance of plan lookups
- **Multi-plan users** - Different plan types
- **Health checks** - Database connectivity under load

```bash
locust -f loadtests/test_plans_quota.py --headless -u 50 -r 5 -t 2m
```

### 4. `test_mixed_scenarios.py` - Realistic User Patterns
Simulates real-world usage:
- **Web users** - Typical SPA behavior patterns
- **API consumers** - High-frequency API calls
- **Admin users** - Elevated privilege operations
- **Monitoring** - Health check frequency

Includes custom load shapes:
- **SpikeLoadShape** - Traffic spikes (3x baseline)
- **GradualRampShape** - Gradual stress testing

```bash
# With spike pattern
locust -f loadtests/test_mixed_scenarios.py SpikeLoadShape --headless -t 10m
```

### 5. `test_database_stress.py` - Database Stress Tests
Stresses the database layer:
- **Connection pool** - Pool exhaustion testing
- **Concurrent reads** - Read scalability
- **Concurrent writes** - Write contention
- **Mixed workload** - 80% reads, 20% writes
- **Recovery** - Burst recovery testing

```bash
locust -f loadtests/test_database_stress.py --headless -u 200 -r 20 -t 5m
```

### 6. `locustfile.py` - Combined Tests
Runs all tests with weighted distribution:
- 40% Web users
- 30% API consumers
- 15% Auth-focused users
- 10% Cache-testing users
- 3% Admin users
- 2% Monitoring

```bash
locust -f loadtests/locustfile.py --headless -u 100 -r 10 -t 5m
```

## Configuration

Configure via environment variables:

```bash
# Target application
export LOADTEST_BASE_URL="http://localhost:8000"
export LOADTEST_API_PREFIX="/api/v1"

# Test user pool
export LOADTEST_USER_COUNT="100"
export LOADTEST_SECRET_KEY="your-jwt-secret-key"

# Test data
export LOADTEST_PLAN_CODES="free,pro,enterprise"
export LOADTEST_FEATURE_CODES="api_calls,ai_generation,exports"
export LOADTEST_ROLE_CODES="user,admin"

# Run configuration
export LOADTEST_SPAWN_RATE="10"
export LOADTEST_RUN_TIME="5m"
```

## Running Headless Tests

For CI/CD integration:

```bash
# Basic headless run
locust -f loadtests/locustfile.py \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --host http://localhost:8000

# With HTML report
locust -f loadtests/locustfile.py \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --html report.html

# With CSV output
locust -f loadtests/locustfile.py \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --csv results
```

## Distributed Testing

For high-scale tests across multiple machines:

```bash
# Start master
locust -f loadtests/locustfile.py --master

# Start workers (on different machines)
locust -f loadtests/locustfile.py --worker --master-host=<master-ip>
```

## Key Metrics to Monitor

### Authentication
- **Auth Failures**: Token expiration/invalidation rate
- **Refresh Success Rate**: Token rotation reliability

### Cache Performance
- **Cache Hit Ratio**: Target >90% in steady state
- **Cold Start Latency**: First request performance
- **Cache Miss Latency**: Database query performance

### Database
- **Connection Pool Usage**: Monitor for exhaustion
- **Query Latency (P95, P99)**: Identify slow queries
- **Error Rate**: Connection timeouts, deadlocks

### System Health
- **Health Check Latency**: Should be <100ms
- **Readiness Probe**: Should reflect actual system state

## Best Practices

1. **Start Small**: Begin with low user counts and ramp up
2. **Monitor Infrastructure**: Watch CPU, memory, connections
3. **Test Incrementally**: Test each module before combining
4. **Use Realistic Data**: Match production user distribution
5. **Set Baselines**: Run tests before and after changes
6. **Test Recovery**: Include failure scenarios

## Interpreting Results

### Good Results
- P95 latency < 500ms
- Error rate < 1%
- Cache hit ratio > 90%
- No connection pool exhaustion

### Warning Signs
- P95 latency > 1000ms
- Error rate > 5%
- Cache hit ratio < 80%
- Frequent connection timeouts

### Critical Issues
- P99 latency > 5000ms
- Error rate > 10%
- Service unavailable responses
- Deadlocks or connection leaks

## Troubleshooting

### High Error Rate
1. Check application logs
2. Verify database connectivity
3. Check rate limiting configuration
4. Increase connection pool size

### High Latency
1. Check database query performance
2. Verify cache is working
3. Check for lock contention
4. Profile slow endpoints

### Connection Issues
1. Increase database pool size
2. Check max connections setting
3. Verify network connectivity
4. Check for connection leaks
