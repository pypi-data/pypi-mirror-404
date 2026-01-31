"""
Cost Katana Python SDK - Logging & Templates Example
Demonstrates how to use AI logging and templates
"""

import cost_katana as ck
from cost_katana import AILogger, TemplateManager, logger
import time


def main():
    # ============================================================================
    # 1. CONFIGURATION
    # ============================================================================

    ck.configure(
        api_key='dak_your_key_here',
        enable_ai_logging=True,
        log_level='debug'
    )

    logger.info('Cost Katana configured with logging and templates')

    # ============================================================================
    # 2. BASIC AI LOGGING
    # ============================================================================

    print('\n=== Basic AI Logging ===\n')

    # All AI calls are automatically logged to Cost Katana dashboard
    response1 = ck.ai('gpt-4', 'Explain quantum computing in one sentence')
    print(f'Response: {response1.text}')
    print(f'Cost: ${response1.cost}')
    # Check your dashboard at https://costkatana.com/ai-logs

    # ============================================================================
    # 3. DISABLE LOGGING FOR SPECIFIC CALLS
    # ============================================================================

    print('\n=== Disable Logging ===\n')

    # Disable logging for sensitive/private calls
    response2 = ck.ai('gpt-4', 'Private query', enable_ai_logging=False)
    print(f'Response (not logged): {response2.text}')

    # ============================================================================
    # 4. TEMPLATE USAGE - LOCAL TEMPLATES
    # ============================================================================

    print('\n=== Local Template Usage ===\n')

    tm = TemplateManager()

    # Define a local template
    tm.define_template({
        'id': 'greeting',
        'name': 'Personalized Greeting',
        'description': 'Generate a personalized greeting',
        'content': 'Generate a {{style}} greeting for {{name}} who works as a {{profession}}.',
        'variables': [
            {'name': 'style', 'required': True},
            {'name': 'name', 'required': True},
            {'name': 'profession', 'required': False, 'defaultValue': 'professional'}
        ]
    })

    # Use the template
    response3 = ck.ai('gpt-4', '', 
        template_id='greeting',
        template_variables={
            'style': 'warm and friendly',
            'name': 'Alice',
            'profession': 'software engineer'
        }
    )

    print(f'Template Response: {response3.text}')
    print(f'Template Used: {response3.templateUsed}')

    # ============================================================================
    # 5. TEMPLATE USAGE - BACKEND TEMPLATES
    # ============================================================================

    print('\n=== Backend Template Usage ===\n')

    # List available templates from backend
    templates = tm.list_templates()
    print(f'Found {len(templates)} templates')

    # Fetch and use a specific template from backend
    # Replace 'template_id_here' with an actual template ID from your dashboard
    # backend_template = tm.get_template('template_id_here')
    # if backend_template:
    #     response4 = ck.ai('gpt-4', '',
    #         template_id=backend_template['id'],
    #         template_variables={} # your variables
    #     )
    #     print(f'Backend Template Response: {response4.text}')

    # ============================================================================
    # 6. CHAT WITH TEMPLATES
    # ============================================================================

    print('\n=== Chat with Templates ===\n')

    session = ck.chat('claude-3-sonnet', system_message='You are a helpful assistant')

    # Regular message
    session.send('Hello!')

    # Message with template
    session.send('',
        template_id='greeting',
        template_variables={
            'style': 'professional',
            'name': 'Bob'
        }
    )

    print(f'Total cost: ${session.total_cost}')
    print(f'Total tokens: {session.total_tokens}')

    # ============================================================================
    # 7. CUSTOM AI LOGGER
    # ============================================================================

    print('\n=== Custom AI Logger ===\n')

    custom_logger = AILogger(
        api_key='dak_your_key',
        project_id='your_project',
        enable_logging=True,
        batch_size=10,        # Flush after 10 logs
        flush_interval=2.0    # Or flush every 2 seconds
    )

    # Log custom AI operations
    custom_logger.log_ai_call({
        'service': 'openai',
        'operation': 'completion',
        'aiModel': 'gpt-4',
        'statusCode': 200,
        'responseTime': 1234,
        'prompt': 'Test prompt',
        'result': 'Test result',
        'inputTokens': 10,
        'outputTokens': 20,
        'totalTokens': 30,
        'cost': 0.001,
        'success': True
    })

    print('Custom log added to buffer')

    # Manual flush
    custom_logger.flush()
    print('Logs flushed to backend')

    # ============================================================================
    # 8. TEMPLATE MANAGER ADVANCED
    # ============================================================================

    print('\n=== Template Manager Advanced ===\n')

    # Define complex template
    tm.define_template({
        'id': 'code-review',
        'name': 'Code Review Template',
        'content': '''Review the following {{language}} code and provide:
1. Code quality assessment
2. Potential bugs or issues
3. Performance improvements
4. Best practices suggestions

Code:
{{code}}

Focus on: {{focus_areas}}''',
        'variables': [
            {'name': 'language', 'required': True},
            {'name': 'code', 'required': True},
            {'name': 'focus_areas', 'defaultValue': 'general quality'}
        ]
    })

    # Resolve template manually
    resolution = tm.resolve_template('code-review', {
        'language': 'Python',
        'code': 'def add(a, b): return a + b',
        'focus_areas': 'type hints and error handling'
    })

    print(f'Resolved prompt: {resolution["prompt"]}')
    print(f'Variables used: {resolution["resolvedVariables"]}')

    # Use resolved prompt
    review_response = ck.ai('gpt-4', resolution['prompt'])
    print(f'Review: {review_response.text}')

    # ============================================================================
    # 9. CONSOLE LOGGING
    # ============================================================================

    print('\n=== Console Logging ===\n')

    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warn('This is a warning message')
    logger.error('This is an error message', Exception('Test error'))

    # Performance timing
    timer = logger.start_timer('API Call')
    time.sleep(0.1)
    timer()  # Logs duration

    # Change log level
    logger.set_level('warn')
    logger.debug('This will not be shown')
    logger.warn('This will be shown')

    logger.info('\n✅ Example completed! Check your Cost Katana dashboard for AI logs.')


if __name__ == '__main__':
    main()

