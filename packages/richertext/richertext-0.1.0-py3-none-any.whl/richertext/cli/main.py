#!/usr/bin/env python3
"""
RicherText CLI - LLM-based CSV Enrichment

Enrich CSV data with LLM-generated classifications, summaries, scores, and reasoning.

Usage:
    richertext init [project_name]
    richertext input.csv --config config.yaml --output enriched.csv
"""

import argparse
import csv
import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv


def find_dotenv():
    """Find .env file by walking up directory tree."""
    current = Path.cwd()
    while current != current.parent:
        env_file = current / ".env"
        if env_file.exists():
            return env_file
        current = current.parent
    return None


# Try to load .env from current dir or parent dirs
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)


# Template files for init command
CONFIG_TEMPLATE = '''provider:
  type: gemini
  model: gemini-2.5-flash-lite

prompts_file: ../prompts/job_postings_prompts.yaml

enrichments:
  # Classify seniority level
  - name: seniority
    type: classifier
    prompt_key: seniority_classifier
    categories:
      - entry
      - mid
      - senior
      - executive
    input_columns: [title, description]
    include_reasoning: false

  # Classify department/function
  - name: department
    type: classifier
    prompt_key: department_classifier
    categories:
      - engineering
      - product
      - design
      - marketing
      - sales
      - customer_success
      - hr
      - finance
      - operations
    input_columns: [title, description]
    include_reasoning: false

  # Tag required skills (multi-label)
  - name: skills
    type: labeler
    prompt_key: skills_labeler
    labels:
      - python
      - javascript
      - sql
      - aws
      - kubernetes
      - ml_ai
      - data_analysis
      - communication
      - leadership
      - sales
      - design
      - marketing
    input_columns: [description]

  # Score the role on multiple dimensions (one scorer each)
  - name: experience_required
    type: scorer
    prompt_key: experience_scorer
    scale_min: 1
    scale_max: 10
    input_columns: [title, description]

  - name: technical_complexity
    type: scorer
    prompt_key: complexity_scorer
    scale_min: 1
    scale_max: 10
    input_columns: [title, description]

  - name: salary_estimate
    type: scorer
    prompt_key: salary_scorer
    scale_min: 1
    scale_max: 10
    input_columns: [title, description]

  # Generate ideal candidate summary
  - name: candidate_profile
    type: summarizer
    prompt_key: candidate_profile
    input_columns: [title, description]
    max_length: 150

  # Example with inline prompt (instead of prompt_key)
  - name: remote_friendly
    type: classifier
    categories:
      - remote
      - hybrid
      - onsite
      - unclear
    input_columns: [description]
    include_reasoning: false
    prompt: |
      Based on this job description, classify the work location policy.

      {description}
'''

PROMPTS_TEMPLATE = '''# Prompt templates for enrichments
# Use {column_name} for variable substitution from input CSV
# Reference these in taskflow.yaml using prompt_key: <key_name>

seniority_classifier: |
  Classify the seniority level of this job posting.

  Title: {title}
  Description: {description}

department_classifier: |
  What department does this role belong to?

  Title: {title}
  Description: {description}

skills_labeler: |
  What skills are required or preferred for this job? Select all that apply.

  {description}

experience_scorer: |
  How much experience is required for this role?
  (1 = entry-level/no experience, 10 = extensive 10+ years)

  Title: {title}
  Description: {description}

complexity_scorer: |
  How technically complex is this role?
  (1 = non-technical, 10 = highly technical/specialized)

  Title: {title}
  Description: {description}

salary_scorer: |
  Estimate the salary level for this role.
  (1 = entry ~$50k, 5 = mid ~$100k, 10 = executive ~$300k+)

  Title: {title}
  Description: {description}

candidate_profile: |
  Write a brief ideal candidate profile for this role in 1-2 sentences.

  Title: {title}
  Description: {description}
'''

SAMPLE_CSV_10 = '''id,title,company,description
1,Senior Software Engineer,TechCorp Inc,"We're looking for a senior software engineer to join our platform team. You'll design and build scalable backend services using Python and Go. 5+ years experience required. Must have experience with AWS, Kubernetes, and distributed systems. Competitive salary and equity."
2,Marketing Manager,GrowthStartup,"Lead our marketing efforts as we scale from Series A to B. You'll own demand generation, content strategy, and brand positioning. Looking for someone with B2B SaaS experience who can work cross-functionally with sales and product. 3-5 years experience preferred."
3,Data Analyst,FinanceHub,"Join our analytics team to help drive data-informed decisions. You'll build dashboards, run A/B tests, and present insights to stakeholders. SQL proficiency required, Python/R a plus. Great opportunity for someone 1-2 years into their career."
4,Chief Technology Officer,HealthAI,"Series B healthtech startup seeks CTO to lead engineering. You'll build and manage a team of 20+ engineers, set technical strategy, and work closely with the CEO. Must have prior VP/CTO experience at a growth-stage company. Healthcare/HIPAA experience preferred."
5,Customer Success Associate,SaaSly,"Entry-level role helping customers get value from our product. You'll handle onboarding calls, answer support tickets, and identify upsell opportunities. No experience required - we'll train you! Great communication skills a must."
6,Product Designer,DesignFirst,"Mid-level product designer for our mobile app team. You'll conduct user research, create wireframes and prototypes, and collaborate with engineers. 2-4 years experience with Figma required. Portfolio review is part of our process."
7,DevOps Engineer,CloudScale,"We need a DevOps engineer to improve our CI/CD pipelines and infrastructure. Terraform, Docker, and AWS expertise required. You'll be on-call rotation and help us achieve 99.99% uptime. 3+ years experience. Remote-friendly."
8,Sales Development Rep,RevenueCo,"SDR role focused on outbound prospecting. You'll research accounts, send personalized outreach, and book meetings for account executives. Base + commission structure. Perfect for recent grads hungry to break into tech sales."
9,Machine Learning Engineer,AILabs,"Build and deploy ML models for our recommendation engine. Strong Python, PyTorch/TensorFlow, and MLOps experience needed. PhD preferred but not required. You'll work on problems at scale with billions of data points."
10,HR Coordinator,PeopleFirst,"Support our growing HR team with recruiting coordination, onboarding, and employee experience initiatives. 1-2 years HR or admin experience preferred. Detail-oriented and organized individuals thrive here. Hybrid role - 3 days in office."
'''

SAMPLE_CSV_100 = '''id,title,company,description
1,Senior Software Engineer,TechCorp Inc,"We're looking for a senior software engineer to join our platform team. You'll design and build scalable backend services using Python and Go. 5+ years experience required. Must have experience with AWS, Kubernetes, and distributed systems. Competitive salary and equity."
2,Marketing Manager,GrowthStartup,"Lead our marketing efforts as we scale from Series A to B. You'll own demand generation, content strategy, and brand positioning. Looking for someone with B2B SaaS experience who can work cross-functionally with sales and product. 3-5 years experience preferred."
3,Data Analyst,FinanceHub,"Join our analytics team to help drive data-informed decisions. You'll build dashboards, run A/B tests, and present insights to stakeholders. SQL proficiency required, Python/R a plus. Great opportunity for someone 1-2 years into their career."
4,Chief Technology Officer,HealthAI,"Series B healthtech startup seeks CTO to lead engineering. You'll build and manage a team of 20+ engineers, set technical strategy, and work closely with the CEO. Must have prior VP/CTO experience at a growth-stage company. Healthcare/HIPAA experience preferred."
5,Customer Success Associate,SaaSly,"Entry-level role helping customers get value from our product. You'll handle onboarding calls, answer support tickets, and identify upsell opportunities. No experience required - we'll train you! Great communication skills a must."
6,Product Designer,DesignFirst,"Mid-level product designer for our mobile app team. You'll conduct user research, create wireframes and prototypes, and collaborate with engineers. 2-4 years experience with Figma required. Portfolio review is part of our process."
7,DevOps Engineer,CloudScale,"We need a DevOps engineer to improve our CI/CD pipelines and infrastructure. Terraform, Docker, and AWS expertise required. You'll be on-call rotation and help us achieve 99.99% uptime. 3+ years experience. Remote-friendly."
8,Sales Development Rep,RevenueCo,"SDR role focused on outbound prospecting. You'll research accounts, send personalized outreach, and book meetings for account executives. Base + commission structure. Perfect for recent grads hungry to break into tech sales."
9,Machine Learning Engineer,AILabs,"Build and deploy ML models for our recommendation engine. Strong Python, PyTorch/TensorFlow, and MLOps experience needed. PhD preferred but not required. You'll work on problems at scale with billions of data points."
10,HR Coordinator,PeopleFirst,"Support our growing HR team with recruiting coordination, onboarding, and employee experience initiatives. 1-2 years HR or admin experience preferred. Detail-oriented and organized individuals thrive here. Hybrid role - 3 days in office."
11,Frontend Developer,WebWorks,"Build beautiful, responsive web applications using React and TypeScript. You'll work closely with designers to implement pixel-perfect UIs. 2-3 years experience required. We use modern tooling: Vite, Tailwind, and testing-library."
12,Account Executive,SalesForce Pro,"Close deals and grow revenue in our mid-market segment. You'll manage the full sales cycle from demo to close. 3+ years B2B SaaS sales experience required. OTE $150-200k with uncapped commission."
13,Backend Engineer,DataFlow,"Join our data platform team building high-throughput streaming systems. Experience with Kafka, Spark, or Flink required. Java or Scala preferred. We process 10M+ events per second."
14,Content Marketing Manager,ContentCo,"Create compelling content that drives organic growth. You'll manage our blog, write case studies, and develop thought leadership pieces. 3-5 years content marketing experience. SEO knowledge a plus."
15,Junior Software Developer,CodeStart,"Great opportunity for bootcamp grads or self-taught developers. You'll learn from senior engineers while building real features. JavaScript/Python basics required. We invest heavily in mentorship."
16,VP of Engineering,ScaleUp,"Lead our 50-person engineering organization through hypergrowth. You'll set technical direction, build culture, and partner with product. 10+ years experience with 5+ in leadership. Series C startup, pre-IPO equity."
17,UX Researcher,UserFirst,"Conduct user interviews, usability tests, and surveys to inform product decisions. You'll synthesize findings into actionable insights. 2-4 years UX research experience. Mixed methods background preferred."
18,Financial Analyst,CapitalGroup,"Support FP&A with budgeting, forecasting, and variance analysis. Advanced Excel and financial modeling skills required. 2-3 years experience in finance or consulting. CPA or MBA a plus."
19,Technical Writer,DocuTech,"Create clear, comprehensive documentation for our developer platform. You'll write API docs, tutorials, and guides. Technical background required - you should be comfortable reading code. Remote OK."
20,Customer Support Specialist,HelpDesk,"First line of support for our customers. You'll troubleshoot issues, answer questions, and escalate when needed. No experience required but tech-savvy preferred. Great stepping stone to CS or product roles."
21,Security Engineer,CyberShield,"Protect our infrastructure and customer data. You'll conduct security assessments, implement controls, and respond to incidents. 3+ years security experience. CISSP or similar certification preferred."
22,Product Manager,ProductLabs,"Own the roadmap for our core product. You'll work with engineering, design, and customers to ship features that matter. 3-5 years PM experience in B2B SaaS. Data-driven decision maker."
23,iOS Developer,MobileFirst,"Build native iOS apps using Swift and SwiftUI. You'll work on features used by millions of users. 3+ years iOS development experience. Published apps required."
24,Recruiter,TalentAcquisition,"Full-cycle recruiting for engineering and product roles. You'll source candidates, manage pipelines, and close offers. 2+ years tech recruiting experience. We're growing fast!"
25,Data Engineer,DataPipeline,"Build and maintain our data infrastructure. You'll design ETL pipelines, optimize queries, and ensure data quality. SQL expert with Python skills. Experience with Snowflake or BigQuery preferred."
26,Operations Manager,OpsExcellence,"Streamline our internal operations as we scale. You'll improve processes, manage vendors, and support the team. 3-5 years ops experience in a fast-paced environment."
27,Android Developer,MobileFirst,"Build native Android apps using Kotlin and Jetpack Compose. You'll work on features used by millions of users. 3+ years Android development experience. Published apps required."
28,Growth Marketing Manager,GrowthLab,"Drive user acquisition through paid channels. You'll manage campaigns across Google, Facebook, and LinkedIn. 3+ years performance marketing experience. Strong analytics skills required."
29,QA Engineer,QualityFirst,"Ensure our product meets the highest quality standards. You'll design test plans, automate tests, and work with developers on bugs. 2-3 years QA experience. Selenium or Cypress knowledge preferred."
30,Executive Assistant,C-Suite Support,"Support our CEO with calendar management, travel, and special projects. Exceptional organizational skills required. 3+ years EA experience preferred. Discretion and professionalism a must."
31,Site Reliability Engineer,ReliableSystems,"Keep our systems running smoothly at scale. You'll build monitoring, automate operations, and respond to incidents. 3+ years SRE or DevOps experience. On-call rotation required."
32,Business Development Rep,PartnerPath,"Generate partnership opportunities through outbound outreach. You'll research potential partners and book meetings for BD managers. Entry-level role with growth potential."
33,Full Stack Developer,StackOverflow,"Work across the entire stack from React frontend to Node.js backend. You'll ship features end-to-end. 3-5 years experience. We value generalists who can adapt quickly."
34,Legal Counsel,LegalEase,"Provide legal support for commercial contracts, employment matters, and compliance. JD required with 4+ years experience. Tech industry experience strongly preferred."
35,Customer Success Manager,SuccessTeam,"Manage a portfolio of enterprise accounts post-sale. You'll drive adoption, renewals, and expansion. 3+ years CSM experience in B2B SaaS. Strong relationship builder."
36,Database Administrator,DataKeepers,"Manage our PostgreSQL and MongoDB databases. You'll handle performance tuning, backups, and disaster recovery. 5+ years DBA experience. High availability expertise required."
37,Brand Designer,BrandStudio,"Shape our visual identity across all touchpoints. You'll create brand assets, marketing materials, and style guides. 3-5 years brand design experience. Strong typography skills."
38,Technical Support Engineer,SupportPro,"Provide technical support for our developer tools. You'll troubleshoot complex issues and work with engineering on fixes. Coding experience required - you'll read logs and debug."
39,Chief Marketing Officer,MarketLeaders,"Lead our marketing organization and drive brand awareness. You'll build the team, set strategy, and own pipeline targets. 15+ years marketing experience with 5+ in leadership."
40,Salesforce Administrator,CRMExperts,"Manage and optimize our Salesforce instance. You'll handle configuration, integrations, and user support. Salesforce Admin certification required. 2-3 years experience."
41,Platform Engineer,PlatformTeam,"Build internal developer tools and platforms. You'll improve developer productivity and standardize infrastructure. 4+ years experience. Kubernetes and IaC expertise required."
42,Demand Generation Manager,DemandGen,"Drive pipeline through integrated campaigns. You'll manage webinars, email nurture, and field marketing. 3-5 years demand gen experience in B2B. Marketing automation expertise required."
43,Junior Data Scientist,DataScience,"Apply ML techniques to business problems. You'll build models, analyze data, and present findings. MS in a quantitative field preferred. Python and SQL required."
44,Office Manager,WorkplaceOps,"Keep our office running smoothly. You'll manage facilities, coordinate events, and support the team. 2+ years office management experience. People person with attention to detail."
45,Solutions Architect,ArchitectPro,"Design technical solutions for enterprise customers. You'll scope implementations, write proposals, and support sales. 5+ years technical experience with customer-facing skills."
46,Copywriter,WordSmith,"Write compelling copy that converts. You'll create landing pages, emails, and ad copy. 2-4 years copywriting experience. B2B tech experience preferred. Portfolio required."
47,Engineering Manager,TeamLead,"Lead a team of 6-8 engineers building our core platform. You'll hire, mentor, and deliver results. 2+ years management experience. Still hands-on with code reviews and architecture."
48,Compliance Analyst,RiskManagement,"Support our compliance program including SOC 2 and GDPR. You'll conduct audits, update policies, and train employees. 2-3 years compliance or audit experience."
49,Partner Marketing Manager,PartnerMarketing,"Drive co-marketing initiatives with our technology partners. You'll manage joint campaigns, events, and content. 3-5 years partner or channel marketing experience."
50,Cloud Architect,CloudExperts,"Design and implement cloud solutions on AWS/GCP/Azure. You'll set standards, review architectures, and mentor engineers. 7+ years experience with cloud certifications."
51,Inside Sales Rep,InsideSales,"Qualify inbound leads and set demos for account executives. You'll be the first point of contact for prospects. Entry-level with growth path to AE. Great communication skills required."
52,Motion Designer,MotionStudio,"Create animated content for marketing and product. You'll produce videos, GIFs, and micro-interactions. 3+ years motion design experience. After Effects and Principle expertise."
53,Scrum Master,AgileTeam,"Facilitate agile ceremonies and remove blockers for engineering teams. You'll coach on best practices and drive continuous improvement. CSM certification required. 2+ years experience."
54,Revenue Operations Analyst,RevOps,"Optimize our go-to-market operations. You'll manage Salesforce data, build reports, and improve processes. 2-3 years RevOps or Sales Ops experience. SQL skills required."
55,Senior Product Designer,DesignLeaders,"Lead design for a major product area. You'll mentor junior designers and set design direction. 5+ years product design experience. Systems thinking and leadership skills."
56,IT Support Specialist,ITHelp,"Provide technical support to employees. You'll troubleshoot hardware/software issues and manage our IT inventory. 1-2 years IT support experience. Patient and helpful attitude."
57,Embedded Systems Engineer,HardwareTech,"Develop firmware for IoT devices. You'll write C/C++ code for resource-constrained systems. 3+ years embedded experience. RTOS knowledge preferred."
58,Social Media Manager,SocialPro,"Manage our social media presence across platforms. You'll create content, engage followers, and track metrics. 2-3 years social media experience. Creative and data-driven."
59,Director of Product,ProductLeadership,"Lead a team of PMs and drive product strategy. You'll work with leadership on company direction. 8+ years product experience with 3+ in leadership. B2B SaaS required."
60,Accounts Payable Specialist,FinanceOps,"Process invoices, manage vendor payments, and reconcile accounts. 2+ years AP experience. Detail-oriented with strong Excel skills. NetSuite experience a plus."
61,AI Research Scientist,AIResearch,"Push the boundaries of AI capabilities. You'll publish papers, develop new techniques, and collaborate with product. PhD in ML/AI required. Strong publication record preferred."
62,Customer Marketing Manager,CustomerMarketing,"Turn customers into advocates. You'll manage case studies, reviews, and reference programs. 3-5 years customer marketing experience. Strong project management skills."
63,Network Engineer,NetworkOps,"Design and maintain our corporate and production networks. You'll handle firewalls, VPNs, and network security. CCNA required, CCNP preferred. 3+ years experience."
64,Technical Recruiter,TechTalent,"Recruit top engineering talent. You'll source, screen, and close candidates. 2+ years tech recruiting experience. Strong technical understanding required."
65,Release Manager,ReleaseOps,"Coordinate software releases across teams. You'll manage release schedules, deployments, and rollbacks. 3+ years release or DevOps experience. Strong communication skills."
66,VP of Sales,SalesLeadership,"Build and lead our sales organization. You'll hire AEs, set quotas, and drive revenue. 10+ years sales experience with 5+ in leadership. Track record of hitting targets."
67,Localization Manager,GlobalOps,"Manage translation and localization of our product. You'll coordinate with translators and ensure quality. 3+ years localization experience. Multiple languages a plus."
68,Business Intelligence Analyst,BITeam,"Build dashboards and reports for business stakeholders. You'll work with data to surface insights. SQL expert with visualization tool experience. Looker or Tableau preferred."
69,Developer Advocate,DevRel,"Be the voice of developers internally and externally. You'll create content, speak at conferences, and gather feedback. Strong technical background with communication skills."
70,Payroll Specialist,PayrollOps,"Process bi-weekly payroll and manage benefits administration. 2+ years payroll experience. ADP or Workday experience preferred. Detail-oriented and confidential."
71,Principal Engineer,TechLeadership,"Provide technical leadership across the organization. You'll solve hard problems, mentor engineers, and shape architecture. 10+ years experience. Staff+ level at a top company."
72,Events Marketing Manager,EventsTeam,"Plan and execute conferences, trade shows, and hosted events. You'll manage budgets, logistics, and measure ROI. 3-5 years events experience. Travel required."
73,Penetration Tester,SecurityTeam,"Conduct security assessments and penetration tests. You'll find vulnerabilities and help teams fix them. 3+ years pentesting experience. OSCP or similar certification."
74,Implementation Consultant,ProServices,"Help customers implement and configure our product. You'll manage projects, train users, and ensure success. 2-4 years implementation or consulting experience. Technical aptitude required."
75,Visual Designer,VisualStudio,"Create beautiful visual designs for marketing and brand. You'll design websites, ads, and collateral. 2-4 years visual design experience. Strong portfolio required."
76,Head of People,PeopleLeadership,"Lead all HR functions including recruiting, benefits, and culture. You'll build the team and programs as we scale. 8+ years HR experience with 3+ in leadership."
77,Golang Developer,GoTeam,"Build high-performance services in Go. You'll work on our core infrastructure handling millions of requests. 3+ years Go experience. Systems programming background preferred."
78,SEO Specialist,SEOTeam,"Improve our organic search rankings and traffic. You'll conduct audits, optimize content, and build links. 2-3 years SEO experience. Technical SEO skills preferred."
79,Field Sales Rep,FieldSales,"Close enterprise deals through in-person meetings and demos. You'll travel to customer sites and work large accounts. 5+ years field sales experience. Proven closer."
80,Instructional Designer,LearningTeam,"Create training content for employees and customers. You'll design courses, videos, and documentation. 3+ years instructional design experience. LMS experience preferred."
81,Performance Marketing Analyst,PerfMarketing,"Optimize paid marketing campaigns through data analysis. You'll manage attribution, run experiments, and report on ROI. 2-3 years analytics experience. SQL required."
82,Chief Financial Officer,FinanceLeadership,"Lead our finance organization including FP&A, accounting, and treasury. You'll partner with CEO on fundraising and strategy. CPA required with 15+ years experience."
83,Customer Education Manager,CustEducation,"Build our customer education program. You'll create courses, certifications, and learning paths. 3-5 years customer education or training experience."
84,Integration Engineer,IntegrationTeam,"Build and maintain integrations with third-party systems. You'll work with APIs, webhooks, and data sync. 3+ years integration experience. REST API expertise required."
85,PR Manager,Communications,"Manage media relations and public communications. You'll pitch stories, handle crises, and build relationships. 3-5 years PR experience. Media contacts in tech preferred."
86,Accounting Manager,AccountingTeam,"Lead our accounting function including close, reporting, and compliance. CPA required with 5+ years experience. Public accounting background preferred."
87,Rust Developer,RustTeam,"Build high-performance systems in Rust. You'll work on our core infrastructure where reliability matters. 2+ years Rust experience. Systems programming background."
88,Channel Sales Manager,ChannelTeam,"Build and manage our partner channel. You'll recruit partners, enable them, and drive indirect revenue. 5+ years channel sales experience."
89,Data Privacy Manager,PrivacyTeam,"Lead our data privacy program. You'll ensure GDPR/CCPA compliance and manage data subject requests. 3-5 years privacy experience. CIPP certification preferred."
90,Creative Director,CreativeLeadership,"Lead our creative team and set visual direction. You'll oversee brand, campaigns, and creative production. 8+ years creative experience with 3+ in leadership."
91,Sales Engineer,SalesEngineering,"Support sales with technical expertise. You'll give demos, answer technical questions, and scope implementations. 3+ years SE or technical experience. Customer-facing skills."
92,Learning & Development Manager,L&DTeam,"Build our internal training and development programs. You'll create content, manage LMS, and measure impact. 3-5 years L&D experience. People development passion."
93,Infrastructure Engineer,InfraTeam,"Build and maintain our cloud infrastructure. You'll automate provisioning and ensure reliability. 3+ years infrastructure experience. AWS and Terraform required."
94,Demand Planning Analyst,SupplyChain,"Forecast demand and optimize inventory. You'll work with sales and operations on planning. 2-3 years demand planning or supply chain experience. Excel expert."
95,User Interface Developer,UITeam,"Build polished UI components and design systems. You'll bridge design and engineering. 3+ years frontend experience with strong design sensibility. CSS expert."
96,Corporate Counsel,LegalTeam,"Handle corporate legal matters including M&A, governance, and securities. JD with 5+ years experience. Tech or startup experience preferred."
97,Tax Manager,TaxTeam,"Manage our tax compliance and planning. You'll handle federal, state, and international taxes. CPA required with 5+ years tax experience. R&D credits experience a plus."
98,Staff Software Engineer,StaffEngineering,"Lead complex technical initiatives across teams. You'll design systems, mentor engineers, and drive quality. 8+ years experience. Track record of technical leadership."
99,Community Manager,CommunityTeam,"Build and nurture our user community. You'll manage forums, organize events, and create programs. 2-3 years community management experience. Passionate about users."
100,Chief People Officer,CPO,"Lead all people functions as a member of the executive team. You'll shape culture, drive talent strategy, and build the org. 15+ years HR with 7+ in leadership. C-suite experience required."
'''

ENV_TEMPLATE = '''# RicherText API Key
# Fill in your Google Gemini API key

GOOGLE_API_KEY=your-api-key-here
'''

GITIGNORE_TEMPLATE = '''# RicherText
.env
input/
output/
rt_input/
rt_output/
*.pyc
__pycache__/
'''

# Documentation templates - loaded from package files
def _get_doc_templates():
    """Load documentation templates from package."""
    import importlib.resources
    docs = {}
    try:
        # Try to read from package resources
        package_root = Path(__file__).parent.parent.parent.parent
        for name, filename in [("readme", "README.md"), ("tutorial", "TUTORIAL.md"), ("enrichments", "ENRICHMENTS.md")]:
            filepath = package_root / filename
            if filepath.exists():
                docs[name] = filepath.read_text()
    except Exception:
        pass
    return docs


def cmd_init(args):
    """Initialize a new RicherText project."""
    # Treat "." or no argument as current directory
    if not args.project_name or args.project_name == ".":
        project_dir = Path.cwd()
        print(f"Initializing RicherText in current directory")
    else:
        project_dir = Path(args.project_name)
        if project_dir.exists():
            print(f"Error: Directory '{project_dir}' already exists", file=sys.stderr)
            sys.exit(1)
        project_dir.mkdir(parents=True)
        print(f"Creating project in {project_dir}/")

    # Determine directory names - use rt_ prefix if standard names exist
    def pick_dir_name(standard, prefixed):
        if (project_dir / standard).exists():
            return prefixed
        return standard

    config_dir = pick_dir_name("taskflows", "rt_taskflows")
    prompts_dir = pick_dir_name("prompts", "rt_prompts")
    input_dir = pick_dir_name("input", "rt_input")
    output_dir = pick_dir_name("output", "rt_output")

    # Create directory structure
    (project_dir / config_dir).mkdir(exist_ok=True)
    (project_dir / prompts_dir).mkdir(exist_ok=True)
    (project_dir / input_dir).mkdir(exist_ok=True)
    (project_dir / output_dir).mkdir(exist_ok=True)

    # Write template files
    config_file = project_dir / config_dir / "job_postings_tasks.yaml"
    if not config_file.exists():
        config_file.write_text(CONFIG_TEMPLATE)
        print(f"  Created {config_file}")

    prompts_file = project_dir / prompts_dir / "job_postings_prompts.yaml"
    if not prompts_file.exists():
        prompts_file.write_text(PROMPTS_TEMPLATE)
        print(f"  Created {prompts_file}")

    sample_file_10 = project_dir / input_dir / "job_postings_10.csv"
    if not sample_file_10.exists():
        sample_file_10.write_text(SAMPLE_CSV_10)
        print(f"  Created {sample_file_10}")

    sample_file_100 = project_dir / input_dir / "job_postings_100.csv"
    if not sample_file_100.exists():
        sample_file_100.write_text(SAMPLE_CSV_100)
        print(f"  Created {sample_file_100}")

    # Only create .env if it doesn't exist
    env_file = project_dir / ".env"
    created_env = False
    if not env_file.exists():
        env_file.write_text(ENV_TEMPLATE)
        print(f"  Created {env_file}")
        created_env = True

    # Only create .gitignore if it doesn't exist
    gitignore_file = project_dir / ".gitignore"
    if not gitignore_file.exists():
        gitignore_file.write_text(GITIGNORE_TEMPLATE)
        print(f"  Created {gitignore_file}")

    # Create docs directory with documentation
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    doc_templates = _get_doc_templates()
    for name, filename in [("readme", "README.md"), ("tutorial", "TUTORIAL.md"), ("enrichments", "ENRICHMENTS.md")]:
        doc_file = docs_dir / filename
        if not doc_file.exists() and name in doc_templates:
            doc_file.write_text(doc_templates[name])
            print(f"  Created {doc_file}")

    print()
    print("Project initialized! Next steps:")
    print()
    if created_env:
        print("  1. Add your API key to .env")
    else:
        print("  1. Make sure your API key is in .env")
    print(f"  2. Run the example (10 records):")
    print()
    if args.project_name and args.project_name != ".":
        print(f"     cd {args.project_name}")
    print(f"     richertext run {input_dir}/job_postings_10.csv --config {config_dir}/job_postings_tasks.yaml -v")
    print()
    print(f"  Or try with 100 records:")
    print(f"     richertext run {input_dir}/job_postings_100.csv --config {config_dir}/job_postings_tasks.yaml -v")
    print()
    print(f"  3. Customize {config_dir}/job_postings_tasks.yaml for your own data")
    print()


def cmd_run(args):
    """Run the enrichment pipeline."""
    from ..utils import load_config, load_prompts, build_provider, build_enrichments
    from ..pipeline import PipelineRunner

    def load_records(filepath: Path):
        """Load records from input CSV, return records and field names."""
        records = []
        with open(filepath, newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            for row in reader:
                records.append(row)
        return records, list(fieldnames)

    def get_processed_pks(output_path: Path, pk_field: str = "id") -> set:
        """Load already processed PKs from output file for resume capability."""
        processed = set()
        if output_path.exists():
            with open(output_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    processed.add(row.get(pk_field, ""))
        return processed

    def log_func(message: str) -> None:
        """Print log message to stderr."""
        print(message, file=sys.stderr)

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    # Default output path
    if args.output is None:
        stem = args.input.stem
        args.output = Path("output") / f"{stem}_enriched.csv"

    # Load config
    config = load_config(args.config)

    # Load records from CSV
    all_records, input_fields = load_records(args.input)

    # Resume capability: skip already processed
    processed_pks = get_processed_pks(args.output, args.pk_field)
    if processed_pks:
        if args.verbose:
            log_func(f"Resuming: {len(processed_pks)} already processed, skipping...")
        all_records = [r for r in all_records if r.get(args.pk_field, "") not in processed_pks]

    if not all_records:
        log_func("All records already processed. Nothing to do.")
        sys.exit(0)

    if args.verbose:
        log_func(f"Processing {len(all_records)} records...")

    # Load prompts if specified
    prompts = {}
    if config.get("prompts_file"):
        prompts_path = args.config.parent / config["prompts_file"]
        if not prompts_path.exists():
            print(f"Error: Prompts file not found: {prompts_path}", file=sys.stderr)
            sys.exit(1)
        prompts = load_prompts(prompts_path)

    # Build provider and enrichments from config
    provider = build_provider(config)
    enrichments = build_enrichments(config, prompts)

    # Calculate workers based on model rate limit if not specified
    if args.workers is None:
        from ..providers import GeminiProvider
        model = config.get("provider", {}).get("model", "gemini-2.5-flash-lite")
        args.workers = GeminiProvider.get_default_workers(model)

    if args.verbose:
        log_func(f"Provider: {provider.model_name}")
        log_func(f"Workers: {args.workers}")
        log_func(f"Enrichments: {[e.name for e in enrichments]}")

    # Run pipeline
    runner = PipelineRunner(
        provider=provider,
        enrichments=enrichments,
        log_func=log_func if args.verbose else None,
        max_workers=args.workers,
    )

    runner.run(
        records=iter(all_records),
        output_path=args.output,
        input_fields=input_fields,
    )

    if args.verbose:
        log_func(f"\nOutput saved to: {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="RicherText - LLM-powered CSV enrichment",
        prog="richertext",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Getting started:
  richertext init my-project    Create a new project with examples
  cd my-project
  richertext run input/job_postings_10.csv --config taskflows/job_postings_tasks.yaml -v
""",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new RicherText project (start here!)",
        description="Create a new project with sample data, config, and prompts.",
    )
    init_parser.add_argument(
        "project_name",
        nargs="?",
        default=None,
        help="Project directory name (default: current directory)"
    )

    # Run command (default behavior)
    run_parser = subparsers.add_parser("run", help="Run enrichment pipeline")
    run_parser.add_argument("input", type=Path, help="Input CSV file")
    run_parser.add_argument("--config", "-c", type=Path, required=True, help="YAML config file")
    run_parser.add_argument("--output", "-o", type=Path, help="Output CSV file (default: output/<input>_enriched.csv)")
    run_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    run_parser.add_argument("--pk-field", default="id", help="Primary key field name for resume (default: id)")
    run_parser.add_argument("--workers", "-w", type=int, default=None, help="Number of parallel workers (default: auto-calculated from model rate limit)")

    # Parse args
    args = parser.parse_args()

    # Handle no command - show help or try legacy mode
    if args.command is None:
        # Check if first arg looks like a file (legacy mode)
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-") and sys.argv[1] != "init":
            # Legacy mode: treat as run command
            sys.argv.insert(1, "run")
            args = parser.parse_args()
        else:
            parser.print_help()
            sys.exit(0)

    # Dispatch to command handler
    if args.command == "init":
        cmd_init(args)
    elif args.command == "run":
        cmd_run(args)


if __name__ == "__main__":
    main()
