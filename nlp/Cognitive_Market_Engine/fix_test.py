#!/usr/bin/env python3
"""Fix test_phase_4.py indentation and event.news_id issues."""

with open('tests/test_phase_4.py', 'r') as f:
    content = f.read()

# First, replace all news_id with event_id
content = content.replace('event.news_id', 'event.event_id')

# Now fix the indentation issue - the duplicated section
# Find and remove duplicate indented blocks
lines = content.split('\n')
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Skip extra-indented aggregator lines that follow properly indented ones
    if line.startswith('        aggregator = BehaviorAggregator()'):
        # Check if we already added a properly indented version
        if fixed_lines and '    aggregator = BehaviorAggregator()' in fixed_lines[-1]:
            # Skip this one
            i += 1
            continue
    
    fixed_lines.append(line)
    i += 1

with open('tests/test_phase_4.py', 'w') as f:
    f.write('\n'.join(fixed_lines))

print("  Fixed test_phase_4.py")
