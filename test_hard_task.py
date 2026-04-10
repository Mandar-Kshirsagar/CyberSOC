"""Test the hard difficulty incident response task"""

import asyncio
from cybersoc.environment import CyberSOCEnv
from cybersoc.models import CyberSOCAction, InvestigationAction


async def main():
    print("🛡️  CyberSOC - Hard Difficulty Task Test")
    print("=" * 70)
    print("Task: Incident Response - Multi-Vector Attack Investigation\n")
    
    # Initialize environment with hard task
    env = CyberSOCEnv(task_name="incident_response")
    print(f"✅ Environment initialized: {env.task_name}")
    print(f"⚠️  Difficulty: HARD")
    print(f"📊 Max steps: {env.max_steps}")
    
    # Reset
    print("\n" + "=" * 70)
    print("📋 Generating incident scenario...")
    obs = await env.reset()
    
    print(f"\n🚨 CRITICAL INCIDENT ALERT")
    print(f"   ID: {obs.current_alert.id}")
    print(f"   Severity: {obs.current_alert.severity}")
    print(f"   Description: {obs.current_alert.description}")
    print(f"\n🖥️  Affected Hosts:")
    for host in obs.current_alert.affected_assets:
        print(f"   - {host}")
    
    print(f"\n📊 Initial Indicators:")
    for indicator in obs.current_alert.raw_data.get('initial_indicators', []):
        print(f"   - {indicator}")
    
    print(f"\n💡 Investigation Hints:")
    for hint in obs.hints or []:
        print(f"   - {hint}")
    
    # Step 1: Query timeline for first host
    print("\n" + "=" * 70)
    print("🔍 Step 1: Querying timeline for first affected host...")
    
    first_host = obs.current_alert.affected_assets[0]
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="query_logs",
            target=first_host,
            confidence=0.8,
            parameters={"query_type": "timeline"}
        )
    )
    
    obs = await env.step(action)
    print(f"✅ Timeline data retrieved for {first_host}")
    print(f"📊 Reward: {env.total_reward:.2f}")
    print(f"⏱️  Steps remaining: {obs.time_remaining}")
    
    # Step 2: Query timeline for second host (correlation)
    if len(obs.current_alert.affected_assets) > 1:
        print("\n" + "=" * 70)
        print("🔍 Step 2: Correlating events across multiple hosts...")
        
        second_host = obs.current_alert.affected_assets[1]
        action = CyberSOCAction(
            action=InvestigationAction(
                action_type="query_logs",
                target=second_host,
                confidence=0.8,
                parameters={"query_type": "timeline"}
            )
        )
        
        obs = await env.step(action)
        print(f"✅ Timeline data retrieved for {second_host}")
        print(f"📊 Reward: {env.total_reward:.2f}")
    
    # Step 3: Check threat intelligence
    print("\n" + "=" * 70)
    print("🔍 Step 3: Checking threat intelligence...")
    
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="check_reputation",
            confidence=0.8,
            parameters={"indicator": "suspicious_activity"}
        )
    )
    
    obs = await env.step(action)
    print(f"✅ Threat intelligence retrieved")
    print(f"📊 Reward: {env.total_reward:.2f}")
    
    # Step 4: Collect forensics
    print("\n" + "=" * 70)
    print("🔍 Step 4: Collecting forensic evidence...")
    
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="collect_forensics",
            target=first_host,
            confidence=0.85
        )
    )
    
    obs = await env.step(action)
    print(f"✅ Forensics collected")
    print(f"📊 Reward: {env.total_reward:.2f}")
    
    # Step 5: Containment decision
    print("\n" + "=" * 70)
    print("🔍 Step 5: Making containment decision...")
    
    # Analyze if this looks like a real attack
    incident_name = obs.current_alert.raw_data.get('incident_name', '')
    is_likely_attack = 'False Positive' not in incident_name
    
    if is_likely_attack:
        print(f"⚠️  Analysis: Indicators suggest active attack")
        print(f"🛡️  Action: Isolating compromised host")
        
        action = CyberSOCAction(
            action=InvestigationAction(
                action_type="isolate_host",
                target=first_host,
                confidence=0.9
            )
        )
        
        obs = await env.step(action)
        print(f"✅ Host isolated: {first_host}")
    else:
        print(f"ℹ️  Analysis: Appears to be legitimate activity")
        print(f"✅ No aggressive containment needed")
    
    print(f"📊 Reward: {env.total_reward:.2f}")
    
    # Step 6: Final conclusion
    print("\n" + "=" * 70)
    print("🎯 Step 6: Making final determination...")
    
    # Reconstruct timeline (simplified for demo)
    timeline = ["initial_access", "execution", "lateral_movement", "impact"]
    classification = "true_positive" if is_likely_attack else "false_positive"
    
    print(f"\n📋 Incident Analysis:")
    print(f"   Classification: {classification}")
    print(f"   Attack Timeline: {' → '.join(timeline)}")
    print(f"   Confidence: 0.80")
    
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="conclude",
            confidence=0.80,
            parameters={
                "conclusion": {
                    "classification": classification,
                    "timeline": timeline,
                }
            }
        ),
        conclusion={
            "classification": classification,
            "timeline": timeline,
            "reasoning": "Multi-stage attack detected across multiple hosts with clear progression",
            "confidence": 0.80
        }
    )
    
    obs = await env.step(action)
    
    # Final results
    print("\n" + "=" * 70)
    print("🏁 INCIDENT RESPONSE COMPLETE")
    print("=" * 70)
    print(f"✅ Episode finished: {env.done}")
    print(f"📊 Final Score: {env.total_reward:.2f}")
    print(f"🎯 Steps taken: {env.current_step}/{env.max_steps}")
    print(f"📜 Actions performed: {len(env.history)}")
    
    # Show investigation timeline
    print(f"\n📋 Investigation Timeline:")
    for i, action in enumerate(env.history, 1):
        target_info = f" → {action.target}" if action.target else ""
        print(f"   {i}. {action.action_type}{target_info} (confidence: {action.confidence:.2f})")
    
    # Performance assessment
    print(f"\n📈 Performance Assessment:")
    if env.total_reward >= 0.5:
        print(f"   ⭐⭐⭐ EXCELLENT - Senior analyst level")
    elif env.total_reward >= 0.3:
        print(f"   ⭐⭐ GOOD - Competent incident response")
    elif env.total_reward >= 0.1:
        print(f"   ⭐ FAIR - Basic investigation completed")
    else:
        print(f"   ❌ NEEDS IMPROVEMENT - Incomplete investigation")
    
    print("\n✅ Hard difficulty task test completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
