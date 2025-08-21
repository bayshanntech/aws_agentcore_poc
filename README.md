# Multi-Agent System: Google ADK with Claude API + Playwright on AWS Bedrock AgentCore

A multi-agent system using Google's Agent Development Kit (ADK) that demonstrates agent-to-agent delegation. The main agent uses Claude API for reasoning, while a specialized Playwright agent handles web automation tasks. This system runs both locally and in AWS Bedrock AgentCore.

## 🏗️ Architecture

**Multi-Agent Workflow:**
1. **Main Agent** (Claude API) → receives user requests and orchestrates the workflow
2. **Playwright Agent** (Browser Automation) → handles web interactions like Google searches
3. **Response Integration** → Main agent analyzes browser results and provides intelligent responses

**Deployment Options:**
- **Local Development**: Multi-agent system runs locally using your API key
- **AWS Deployment**: Same system runs in Bedrock AgentCore using secure outbound identity
- **LLM Model**: Claude 3.5 Sonnet via Anthropic API (not AWS Bedrock models)
- **Browser Automation**: Playwright with Chromium for headless web interactions

## 📋 Prerequisites

- Python 3.10+
- AWS CLI configured with appropriate permissions
- Anthropic Claude API key
- AWS Bedrock AgentCore access
- **Playwright browsers** (automatically installed via `make setup`)

## 🚀 Quick Start

### 1. Complete Setup (Everything Automated!)

```bash
git clone <your-repo>
cd aws_agentcore_poc
make setup  # Sets up everything: deps, virtual env, IAM role, etc.
```

### 2. Configure Claude API Key (Secure Methods)

The agent uses **secure credential management** with multiple fallback options:

**Option A: AWS Secrets Manager (Recommended for Production)**
- API key is securely stored in AWS Secrets Manager
- No configuration needed - works automatically if you have the secret ARN configured

**Option B: Environment Variable (Local Development Only)**
- Set `ANTHROPIC_API_KEY` in your `.env` file:

```bash
# Claude API Configuration (LOCAL DEVELOPMENT ONLY)
# ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# AWS Secrets Manager (Production - already configured)
SECRETS_MANAGER_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:your-secret

# AWS Configuration (optional - uses AWS CLI if not set)
AWS_REGION=us-east-1
AWS_PROFILE=default
```

**🔐 Security Priority Order:**
1. AgentCore Outbound Identity (when running in AgentCore)
2. AWS Secrets Manager (production-ready)  
3. Environment Variable (local development fallback)

### 3. Test Locally

```bash
make run  # Test your agent locally
```

### 4. Deploy to AWS (3 commands!)

```bash
make configure  # Configure AgentCore (auto-detects IAM role)
make launch     # Deploy to AWS Bedrock AgentCore  
make invoke     # Test your deployed agent
```

Expected output:
```
🚀 Starting Claude Hello World ADK Agent...

📄 Agent Response:
{
  "agent_response": "Hello! It's nice to meet you. I'm Claude, an AI assistant created by Anthropic. How are you doing today?",
  "prompt_used": "please say hello",
  "model": "claude-3-5-sonnet-20241022",
  "status": "success"
}
```

## 📁 Project Structure

```
aws_agentcore_poc/
├── main.py                 # Main ADK agent implementation
├── agent_example.py        # AgentCore entry point handler
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── Makefile               # Development automation
├── .env.template          # Environment template
├── .env                   # Your environment variables (created by make setup)
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🔧 Development Commands

| Command                                                                    | Description |
|----------------------------------------------------------------------------|-------------|
| `make setup`                                                               | Set up development environment |
| `make run PROMPT="Summarise the headlines on https://www.abc.net.au/news"` | Run the agent locally |
| `make test`                                                                | Test the agent |
| `make package`                                                             | Package for AWS deployment |
| `make clean`                                                               | Clean build artifacts |
| `make help`                                                                | Show all available commands |

## ☁️ AWS Bedrock AgentCore Deployment

### Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Docker or Finch** installed for local testing
3. **IAM Role** for AgentCore execution with necessary permissions
4. **Outbound Identity**: "Anthropic-Key-Diego" (you mentioned having this set up)

### 🎯 **Super Simple 3-Step Deployment:**

#### Step 1: Complete Setup (Everything in One Command!)
```bash
make setup  # Installs deps + creates IAM role automatically
```

#### Step 2: Configure AgentCore
```bash
make configure  # Auto-detects the IAM role created in Step 1
```

#### Step 3: Deploy to AWS
```bash
make launch     # Deploy to AgentCore
make invoke     # Test your deployed agent
```

### 🔍 **What `make setup` Does Automatically:**
- ✅ Creates Python virtual environment
- ✅ Installs all dependencies (ADK, AgentCore, Claude API)  
- ✅ Creates `.env` file template
- ✅ Auto-detects your AWS account
- ✅ Creates `AgentCoreExecutionRole` with proper permissions
- ✅ Shows you the IAM role ARN for reference

### 🧪 **Optional: Test Locally First**
```bash
make launch-local  # Test with AgentCore locally
make status        # Check deployment status
```

### Alternative: Manual Deployment Commands

If you prefer to use the AgentCore CLI directly:

```bash
# Configure
agentcore configure --entrypoint agent_example.py --execution-role YOUR_IAM_ROLE_ARN

# Test locally
agentcore launch -l

# Deploy to AWS
agentcore launch

# Test
agentcore invoke '{"prompt": "Hello from AgentCore!"}'

# Check status
agentcore status
```

## 🛠️ How It Works

### Local Execution
1. Agent tries AgentCore outbound identity (if available)
2. Falls back to AWS Secrets Manager for API key
3. Final fallback to `.env` file for local development
4. Creates Anthropic client with retrieved API key
5. ADK agent calls Claude API directly
6. Returns formatted JSON response

### AWS AgentCore Execution  
1. AgentCore loads the packaged agent
2. **Primary**: Uses outbound identity for secure API key management
3. **Fallback**: Uses AWS Secrets Manager if outbound identity unavailable
4. Agent processes requests through proper entry point
5. Same agent code calls Claude API with secure credentials
6. Returns response through AgentCore runtime

## 🔐 Security Best Practices

- ✅ **No hardcoded credentials** anywhere in the codebase
- ✅ **AWS Secrets Manager** for production API key storage

- ✅ **Environment variables** only for local development fallback
- ✅ **Multi-tier credential resolution** with secure priorities
- ✅ **JSON secret parsing** supporting multiple key formats
- ✅ **IAM permissions** properly configured for Secrets Manager
- ✅ `.env` file excluded from git

## 🧪 Testing

### Local Testing
```bash
make test
```

### Manual Testing
```bash
python main.py
```

### Integration Testing
Deploy to AgentCore and test through AWS console or API calls.

## 🐛 Troubleshooting

### Common Issues

1. **Missing API Key**
   - Error: `ANTHROPIC_API_KEY is required`
   - Solution: Add your API key to `.env` file

2. **Import Errors**
   - Error: `ModuleNotFoundError: No module named 'google.adk'`
   - Solution: Run `make setup` to install dependencies

3. **AWS Permissions**
   - Error: Permission denied for AgentCore operations
   - Solution: Ensure your AWS CLI is configured with proper IAM permissions

4. **Claude API Errors**
   - Error: Authentication failed
   - Solution: Verify your ANTHROPIC_API_KEY is valid and active

## 📚 Additional Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [AWS Bedrock AgentCore Guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/)

## 🚢 Next Steps

  ❌ What's Not Working:

   AgentCore has an issue detectin' Docker on yer system, even though Docker is clearly runnin'. This might be a bug in the AgentCore SDK or a path issue.

  Deployment Issue:
  - Our prompt forwarding fixes are only in local files (uncommitted)
  - Current deployed version still has hardcoded "hello world"
  - AgentCore isn't detecting Docker (even though Docker is running)
  - Can't use --local-build or --local deployment modes

  Current State:
  When you run agentcore invoke '{"prompt": "Search Melbourne Weather"}', it still searches for "hello world" because the deployed version doesn't have our fixes.

