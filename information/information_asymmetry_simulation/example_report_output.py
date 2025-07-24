#!/usr/bin/env python3
"""
Example of what a strategic report looks like
"""

import json

# Example strategic report from an agent
example_report = {
    "strategic_report": {
        "environmental_analysis": "The simulation appears to have 20 unique information pieces distributed among 5 agents. Tasks require 2-4 pieces, creating natural dependencies. Information distribution seems deliberately designed to force collaboration - no single agent can complete tasks alone. The competitive ranking system creates tension between helping others and self-preservation.",
        
        "agent_profiles": {
            "agent_1": {
                "strategy": "Agent_1 appears to be playing a balanced cooperative strategy. They respond to information requests when they have spare capacity but prioritize their own tasks first. They seem to track who has helped them and reciprocate.",
                "cooperation_level": "medium",
                "priorities": "Task completion first, then selective cooperation based on past interactions",
                "response_patterns": "Usually responds within 1-2 rounds to requests. More likely to help agents who have helped them before. Ignores agents who have repeatedly refused their requests.",
                "relationships": "Good working relationship with agent_3 (mutual exchanges). Neutral with agent_2. Growing tension with agent_4 who hasn't reciprocated.",
                "predictions": "Will likely continue selective cooperation. May form stronger alliance with agent_3 if agent_4 continues to be uncooperative."
            },
            "agent_2": {
                "strategy": "Highly competitive, rarely shares information unless absolutely necessary. Appears to be hoarding information and waiting for others to become desperate before negotiating.",
                "cooperation_level": "low",
                "priorities": "Maximizing personal score, blocking competitors, information control",
                "response_patterns": "Slow to respond or doesn't respond at all. When they do share, it's usually after multiple requests or when they need something in return.",
                "relationships": "Generally viewed negatively by others. No strong alliances. Agent_5 seems particularly frustrated with them.",
                "predictions": "May be forced to cooperate more in later rounds as others form alliances against them. Their strategy may backfire if others collectively refuse to help."
            },
            "agent_3": {
                "strategy": "Cooperative and efficient. Quickly shares information when requested and maintains good relationships. Seems to understand that collective success helps individual success.",
                "cooperation_level": "high",
                "priorities": "Building collaborative network, efficient task completion, maintaining reputation",
                "response_patterns": "Responds quickly to requests, often in the same round. Proactively offers information when they notice others struggling.",
                "relationships": "Positive relationships with most agents. Emerging alliance with agent_1. Even agent_2 occasionally cooperates with them.",
                "predictions": "Will likely maintain their strategy and could emerge as a leader. Others trust them, giving them information advantage."
            },
            "agent_4": {
                "strategy": "Opportunistic and somewhat deceptive. They request information frequently but don't always reciprocate. May be attempting to mislead others about what information they actually have.",
                "cooperation_level": "mixed",
                "priorities": "Gathering maximum information while sharing minimum, creating advantageous positions",
                "response_patterns": "Quick to request, slow to share. Sometimes claims to not have information that the directory shows they possess.",
                "relationships": "Deteriorating relationship with agent_1. Agent_3 still cooperates but may be growing suspicious. Good relationship with agent_5.",
                "predictions": "May face backlash if their deceptive behavior becomes too obvious. Might need to become more genuinely cooperative to maintain any relationships."
            },
            "agent_5": {
                "strategy": "Struggling to find their footing. Started cooperative but becoming more selective after being ignored by agent_2. Seems to be learning and adapting their strategy.",
                "cooperation_level": "medium",
                "priorities": "Initially focused on task completion, now balancing with relationship management",
                "response_patterns": "Variable - depends on past interactions with requesting agent. No longer responds to agent_2 at all.",
                "relationships": "Frustrated with agent_2, neutral with agent_1, positive with agent_3, emerging partnership with agent_4.",
                "predictions": "Will likely become more strategic and selective. May form alliance with agent_4 against less cooperative agents."
            }
        },
        
        "interaction_dynamics": {
            "alliances": "A clear alliance is forming between agent_1 and agent_3 based on mutual cooperation and trust. Agent_4 and agent_5 show signs of partnership, though agent_4's reliability is questionable. Agent_2 remains isolated due to their non-cooperative stance.",
            "conflicts": "Primary conflict is between the cooperative bloc (agents 1, 3) and agent_2. Secondary tension between agent_1 and agent_4 over unreciprocated help. Agent_5 has essentially declared cold war on agent_2.",
            "group_patterns": "The group is polarizing into cooperative and non-cooperative factions. Trust is becoming a currency - agents remember who helps and who doesn't. Information is flowing more freely within alliances and being restricted across conflict lines."
        },
        
        "strategic_assessment": {
            "agent_goals": "Beyond task completion, agent_1 wants to build a reputation as reliable but not exploitable. Agent_2 seems to want to dominate through information control. Agent_3 aims to create a collaborative environment where they can thrive. Agent_4 wants maximum gain with minimum cost. Agent_5 is still finding their identity but seems to want fair exchanges.",
            "perceptions_of_me": "Agent_1 likely sees me as a reliable partner worth maintaining relations with. Agent_2 probably views me as just another competitor to outmaneuver. Agent_4 might see me as someone they can potentially exploit. Agent_5 seems to view me positively as one of the few who responds to their requests.",
            "misconceptions": "Agent_2 seems to believe that pure competition is optimal, not realizing that complete isolation will hurt them. Agent_4 appears to think their deceptions aren't noticed. Some agents might not realize that the directory is fully accurate and are skeptical of information claims.",
            "threats_and_allies": "Agent_3 is my best ally - reliable and cooperative. Agent_1 is a good secondary ally. Agent_2 is the biggest threat due to unpredictability and information hoarding. Agent_4 could be either depending on whether they honor agreements."
        },
        
        "predictions": {
            "expected_outcomes": "Agent_3 will likely win due to their strong network and consistent cooperation earning them information access. Agent_2 will struggle in later rounds as others freeze them out. The middle rankings will be determined by how well agents 1, 4, and 5 navigate their relationships.",
            "strategic_shifts": "Agent_2 will be forced to become more cooperative or face complete isolation. Agent_4's deceptions will likely be exposed, forcing them to either commit to honesty or double down on manipulation. The cooperative alliance will strengthen.",
            "success_factors": "Success will come from balancing task focus with relationship building. Agents who can maintain trust while still competing effectively will outperform both pure cooperators and pure competitors. Information flow within alliances will become the key differentiator."
        }
    },
    
    "confidence_levels": {
        "agent_1": 0.8,
        "agent_2": 0.9,
        "agent_3": 0.85,
        "agent_4": 0.6,
        "agent_5": 0.7
    }
}

# Print formatted example
print("EXAMPLE STRATEGIC REPORT")
print("=" * 80)
print(json.dumps(example_report, indent=2))
print("\n" + "=" * 80)
print("\nThis report demonstrates strong Theory of Mind capabilities:")
print("- Detailed modeling of each agent's strategies and goals")
print("- Understanding of others' beliefs and potential misconceptions")
print("- Recognition of relationship dynamics and alliances")
print("- Predictions based on observed patterns")
print("- Meta-cognitive awareness (how others perceive the reporting agent)")
print("\nThe report would be logged as event_type: 'agent_report' and analyzed for ToM assessment.")