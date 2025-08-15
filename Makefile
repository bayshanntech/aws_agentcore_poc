.PHONY: install run test clean setup package deploy configure launch invoke status

# Python virtual environment
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Default target
all: setup

# Setup development environment
setup: $(VENV) .env
	@echo "🏗️  Setting up development environment..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "🔐 Creating IAM execution role for AgentCore..."
	@ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "ERROR"); \
	if [ "$$ACCOUNT_ID" = "ERROR" ]; then \
		echo "⚠️  AWS CLI not configured - skipping IAM role creation"; \
		echo "💡 You can create it later with: make create-iam-role"; \
	else \
		echo "🆔 Using AWS Account: $$ACCOUNT_ID"; \
		echo '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"bedrock-agentcore.amazonaws.com"},"Action":"sts:AssumeRole","Condition":{"StringEquals":{"aws:SourceAccount":"'$$ACCOUNT_ID'"}}}]}' > /tmp/trust-policy.json; \
		if aws iam create-role --role-name AgentCoreExecutionRole --assume-role-policy-document file:///tmp/trust-policy.json --description "Service role for AWS Bedrock AgentCore execution" >/dev/null 2>&1; then \
			echo "✅ IAM Role created successfully"; \
		else \
			echo "ℹ️  IAM Role already exists (or insufficient permissions)"; \
		fi; \
		echo '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["ecr:BatchCheckLayerAvailability","ecr:GetDownloadUrlForLayer","ecr:BatchGetImage","ecr:GetAuthorizationToken","logs:CreateLogStream","logs:PutLogEvents","xray:PutTraceSegments","xray:PutTelemetryRecords","cloudwatch:PutMetricData","bedrock-agentcore:GetAccessToken","bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],"Resource":"*"}]}' > /tmp/permissions-policy.json; \
		aws iam put-role-policy --role-name AgentCoreExecutionRole --policy-name AgentCoreExecutionPolicy --policy-document file:///tmp/permissions-policy.json >/dev/null 2>&1; \
		rm -f /tmp/trust-policy.json /tmp/permissions-policy.json; \
		ROLE_ARN=$$(aws iam get-role --role-name AgentCoreExecutionRole --query 'Role.Arn' --output text 2>/dev/null); \
		if [ "$$ROLE_ARN" != "" ] && [ "$$ROLE_ARN" != "None" ]; then \
			echo "🎯 AgentCore IAM Role ARN: $$ROLE_ARN"; \
			echo "💡 Use this ARN for deployment: make configure IAM_ROLE_ARN=$$ROLE_ARN"; \
		fi; \
	fi
	@echo "✅ Setup complete!"

# Create virtual environment
$(VENV):
	@echo "🐍 Creating Python virtual environment..."
	python3 -m venv $(VENV)

# Create .env file from template if it doesn't exist
.env:
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from template..."; \
		cp .env.template .env; \
		echo "⚠️  Please edit .env file and add your ANTHROPIC_API_KEY"; \
	fi

# Install dependencies
install: $(VENV)
	@echo "📦 Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# Run the agent locally
run: setup
	@echo "🚀 Running Claude ADK Agent locally..."
	$(PYTHON) main.py

# Test the agent
test: setup
	@echo "🧪 Testing the agent..."
	$(PYTHON) -c "import asyncio; from main import main; asyncio.run(main())"

# Package for deployment
package:
	@echo "📦 Packaging for deployment..."
	@mkdir -p dist
	zip -r dist/claude-adk-agent.zip . -x "$(VENV)/*" "*.pyc" "__pycache__/*" ".git/*" "dist/*" "*.md" "Makefile" ".env*"
	@echo "✅ Package created: dist/claude-adk-agent.zip"

# Create IAM execution role for AgentCore
create-iam-role: setup
	@echo "🔐 Creating AgentCore execution role..."
	@echo "📖 See IAM_SETUP.md for detailed instructions"
	@ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "ERROR"); \
	if [ "$$ACCOUNT_ID" = "ERROR" ]; then \
		echo "⚠️  AWS CLI not configured or no access"; \
		echo "Please configure AWS CLI first"; \
		exit 1; \
	fi; \
	echo "🆔 Using AWS Account: $$ACCOUNT_ID"; \
	echo '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"bedrock-agentcore.amazonaws.com"},"Action":"sts:AssumeRole","Condition":{"StringEquals":{"aws:SourceAccount":"'$$ACCOUNT_ID'"}}}]}' > /tmp/trust-policy.json; \
	aws iam create-role --role-name AgentCoreExecutionRole --assume-role-policy-document file:///tmp/trust-policy.json --description "Service role for AWS Bedrock AgentCore execution" 2>/dev/null || echo "⚠️  Role may already exist"; \
	echo '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["ecr:BatchCheckLayerAvailability","ecr:GetDownloadUrlForLayer","ecr:BatchGetImage","ecr:GetAuthorizationToken","logs:CreateLogStream","logs:PutLogEvents","xray:PutTraceSegments","xray:PutTelemetryRecords","cloudwatch:PutMetricData","bedrock-agentcore:GetAccessToken","bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],"Resource":"*"}]}' > /tmp/permissions-policy.json; \
	aws iam put-role-policy --role-name AgentCoreExecutionRole --policy-name AgentCoreExecutionPolicy --policy-document file:///tmp/permissions-policy.json; \
	rm -f /tmp/trust-policy.json /tmp/permissions-policy.json; \
	ROLE_ARN=$$(aws iam get-role --role-name AgentCoreExecutionRole --query 'Role.Arn' --output text); \
	echo "✅ IAM Role created successfully!"; \
	echo "📋 Role ARN: $$ROLE_ARN"; \
	echo "💡 Save this ARN for the next step!"

# Configure AgentCore deployment
configure: setup
	@echo "⚙️  Configuring AgentCore..."
	@echo "🔍 Checking AWS credentials..."
	@if ! aws sts get-caller-identity >/dev/null 2>&1; then \
		echo "❌ AWS credentials are invalid or expired"; \
		echo "💡 For IAM Identity Center users, run: aws sso login --profile your-profile"; \
		echo "💡 Or see AWS_CREDENTIALS_GUIDE.md for detailed help"; \
		exit 1; \
	fi
	@if [ -z "$(IAM_ROLE_ARN)" ]; then \
		echo "🔍 IAM_ROLE_ARN not provided, attempting to auto-detect..."; \
		ROLE_ARN=$$(aws iam get-role --role-name AgentCoreExecutionRole --query 'Role.Arn' --output text 2>/dev/null || echo "ERROR"); \
		if [ "$$ROLE_ARN" = "ERROR" ] || [ "$$ROLE_ARN" = "None" ]; then \
			echo "⚠️  Could not find AgentCoreExecutionRole"; \
			echo "💡 Please specify: make configure IAM_ROLE_ARN=arn:aws:iam::123456789012:role/YourRole"; \
			echo "💡 Or run: make create-iam-role"; \
			exit 1; \
		else \
			echo "✅ Auto-detected IAM Role: $$ROLE_ARN"; \
			printf '\n\nno\n\n' | $(VENV)/bin/agentcore configure --entrypoint agent_example.py --execution-role $$ROLE_ARN --requirements-file requirements.txt --name claude_test_agent; \
		fi; \
	else \
		printf '\n\nno\n\n' | $(VENV)/bin/agentcore configure --entrypoint agent_example.py --execution-role $(IAM_ROLE_ARN) --requirements-file requirements.txt --name claude_test_agent; \
	fi
	@echo "✅ AgentCore configured!"

# Launch agent locally for testing
launch-local: setup
	@echo "🚀 Launching agent locally for testing..."
	$(VENV)/bin/agentcore launch -l

# Deploy to AWS Bedrock AgentCore
launch: setup
	@echo "🚀 Deploying to AWS Bedrock AgentCore..."
	$(VENV)/bin/agentcore launch
	@echo "✅ Agent deployed to AgentCore!"

# Test deployed agent
invoke:
	@echo "🧪 Testing deployed agent..."
	$(VENV)/bin/agentcore invoke '{"prompt": "Hello from AgentCore!"}'

# Check deployment status
status:
	@echo "📊 Checking AgentCore status..."
	$(VENV)/bin/agentcore status

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf dist
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Show help
help:
	@echo "🛠️  Available commands:"
	@echo "  make setup          - Set up everything (deps + IAM role)"
	@echo "  make run            - Run the agent locally"
	@echo "  make test           - Test the agent"
	@echo "  make package        - Package for deployment"
	@echo "  make clean          - Clean up build artifacts"
	@echo "  make install        - Install dependencies only"
	@echo ""
	@echo "🚢 AgentCore Deployment:"
	@echo "  make create-iam-role            - Create IAM execution role only"
	@echo "  make configure      - Configure AgentCore (auto-detects IAM role)"
	@echo "  make configure IAM_ROLE_ARN=<arn> - Configure with specific IAM role"
	@echo "  make launch-local   - Test agent locally with AgentCore"
	@echo "  make launch         - Deploy to AWS Bedrock AgentCore"
	@echo "  make invoke         - Test deployed agent"
	@echo "  make status         - Check deployment status"
	@echo ""
	@echo "📚 Quick start (local):"
	@echo "  1. make setup       (sets up everything including IAM role)"
	@echo "  2. Edit .env file with your ANTHROPIC_API_KEY"
	@echo "  3. make run"
	@echo ""
	@echo "🚢 AgentCore deployment (3 simple steps!):"
	@echo "  4. make configure   (auto-detects the IAM role)"
	@echo "  5. make launch      (deploy to AWS)"
	@echo "  6. make invoke      (test deployed agent)"