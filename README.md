# Google ADK Agent with Claude API on AWS Bedrock AgentCore

A simple "Hello World" example using Google's Agent Development Kit (ADK) that calls Claude API directly instead of AWS hosted models. This agent runs both locally and in AWS Bedrock AgentCore.

## 🏗️ Architecture

- **Local Development**: ADK agent calls Claude API directly using your API key
- **AWS Deployment**: Same agent runs in Bedrock AgentCore using outbound identity
- **Model**: Claude 3.5 Sonnet via Anthropic API (not AWS Bedrock models)

## 📋 Prerequisites

- Python 3.10+
- AWS CLI configured with appropriate permissions
- Anthropic Claude API key
- AWS Bedrock AgentCore access

## 🚀 Quick Start

### 1. Complete Setup (Everything Automated!)

```bash
git clone <your-repo>
cd aws_agentcore_poc
make setup  # Sets up everything: deps, virtual env, IAM role, etc.
```

### 2. Add Your Claude API Key

Edit the `.env` file that was created:

```bash
# Claude API Configuration (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# AWS Configuration (optional - uses AWS CLI if not set)
AWS_REGION=us-east-1
AWS_PROFILE=default
```

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

| Command | Description |
|---------|-------------|
| `make setup` | Set up development environment |
| `make run` | Run the agent locally |
| `make test` | Test the agent |
| `make package` | Package for AWS deployment |
| `make clean` | Clean build artifacts |
| `make help` | Show all available commands |

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
1. Agent loads configuration from `.env` file
2. Creates Anthropic client with your API key
3. ADK agent calls Claude API directly
4. Returns formatted JSON response

### AWS AgentCore Execution
1. AgentCore loads the packaged agent
2. Uses outbound identity for secure API key management
3. Lambda handler processes requests
4. Same agent code calls Claude API
5. Returns response through AgentCore runtime

## 🔐 Security Best Practices

- ✅ API keys stored in environment variables
- ✅ Outbound identity used in AWS
- ✅ No hardcoded credentials in code
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

1. **Extend Functionality**: Add more tools and capabilities to your agent
2. **Add Persistence**: Integrate with AWS S3 or DynamoDB for state management
3. **Monitoring**: Add CloudWatch logging and metrics
4. **CI/CD**: Set up automated deployment pipeline
5. **Multi-Agent**: Create agent workflows with multiple ADK agents

---

*Built with ⚓ by Captain Blackwater - May your deployments be smooth sailing!*