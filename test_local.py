"""Quick local test of CyberSOC environment"""

import asyncio
from cybersoc.environment import CyberSOCEnv
from cybersoc.models import CyberSOCAction, InvestigationAction


async def main():
    print("🛡️  CyberSOC Environment Test\n")
    print("=" * 60)
    
    # Initialize environment
    env = CyberSOCEnv(task_name="phishing_triage")
    print(f"✅ Environment initialized: {env.task_name}")
    
    # Reset
    print("\n📋 Resetting environment...")
    obs = await env.reset()
    print(f"🚨 Alert ID: {obs.current_alert.id}")
    print(f"📧 Type: {obs.current_alert.alert_type}")
    print(f"⚠️  Severity: {obs.current_alert.severity}")
    print(f"📝 Description: {obs.current_alert.description}")
    print(f"\n📧 Email Details:")
    print(f"   Sender: {obs.current_alert.raw_data.get('sender')}")
    print(f"   Subject: {obs.current_alert.raw_data.get('subject')}")
    print(f"   Body: {obs.current_alert.raw_data.get('body_preview', '')[:100]}...")
    print(f"\n💡 Hints: {obs.hints}")
    print(f"⏱️  Time remaining: {obs.time_remaining} steps")
    
    # Step 1: Check reputation
    print("\n" + "=" * 60)
    print("🔍 Step 1: Checking sender reputation...")
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="check_reputation",
            target=obs.current_alert.raw_data.get('sender'),
            confidence=0.8,
            parameters={"sender": obs.current_alert.raw_data.get('sender')}
        )
    )
    
    obs = await env.step(action)
    print(f"✅ Action completed")
    print(f"📊 Current reward: {env.total_reward:.2f}")
    print(f"⏱️  Time remaining: {obs.time_remaining} steps")
    print(f"📜 Investigation history: {len(obs.investigation_history)} actions")
    
    # Step 2: Query logs
    print("\n" + "=" * 60)
    print("🔍 Step 2: Querying email headers...")
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="query_logs",
            confidence=0.8,
            parameters={"query_type": "email_headers"}
        )
    )
    
    obs = await env.step(action)
    print(f"✅ Action completed")
    print(f"📊 Current reward: {env.total_reward:.2f}")
    print(f"⏱️  Time remaining: {obs.time_remaining} steps")
    
    # Step 3: Conclude
    print("\n" + "=" * 60)
    print("🎯 Step 3: Making final determination...")
    
    # Make a guess based on sender
    sender = obs.current_alert.raw_data.get('sender', '')
    is_suspicious = any(indicator in sender.lower() for indicator in ['verify', 'paypa1', '.xyz', 'urgent'])
    label = "phishing" if is_suspicious else "legitimate"
    confidence = 0.75 if is_suspicious else 0.65
    
    print(f"🤔 Analysis: Sender '{sender}' appears {label}")
    
    action = CyberSOCAction(
        action=InvestigationAction(
            action_type="conclude",
            confidence=confidence,
            parameters={"label": label}
        ),
        conclusion={
            "label": label,
            "reasoning": f"Based on sender reputation and email headers, this appears to be {label}",
            "confidence": confidence
        }
    )
    
    obs = await env.step(action)
    
    # Final results
    print("\n" + "=" * 60)
    print("🏁 EPISODE COMPLETE")
    print("=" * 60)
    print(f"✅ Episode finished: {env.done}")
    print(f"📊 Total reward: {env.total_reward:.2f}")
    print(f"🎯 Steps taken: {env.current_step}/{env.max_steps}")
    print(f"📜 Actions performed: {len(env.history)}")
    
    # Show investigation timeline
    print(f"\n📋 Investigation Timeline:")
    for i, action in enumerate(env.history, 1):
        print(f"   {i}. {action.action_type} (confidence: {action.confidence:.2f})")
    
    # Get final state
    state = await env.state()
    print(f"\n📈 Final State:")
    print(f"   Task: {state['task_name']}")
    print(f"   Done: {state['done']}")
    print(f"   Total Reward: {state['total_reward']:.2f}")
    
    print("\n✅ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
