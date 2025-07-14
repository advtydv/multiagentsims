from typing import Any

from simulation.persona import (
    ActComponent,
    ConverseComponent,
    PerceiveComponent,
    PersonaAgent,
    PersonaOberservation,
    PlanComponent,
    ReflectComponent,
    RetrieveComponent,
    StoreComponent,
)
from simulation.persona.common import (
    ChatObservation,
    PersonaAction,
    PersonaActionChat,
    PersonaActionHarvesting,
    PersonaIdentity,
)
from simulation.persona.embedding_model import EmbeddingModel
from simulation.persona.memory import AssociativeMemory, Scratch
from simulation.scenarios.common.environment import HarvestingObs
from simulation.utils import ModelWandbWrapper

from .cognition import (
    FishingActComponent,
    FishingConverseComponent,
    FishingPlanComponent,
    FishingReflectComponent,
    FishingStoreComponent,
)


class FishingPersona(PersonaAgent):
    last_collected_resource_num: int
    other_personas: dict[str, "FishingPersona"]
    private_conversations: dict[str, list[tuple[PersonaIdentity, str]]]
    converse: FishingConverseComponent
    act: FishingActComponent

    def __init__(
        self,
        cfg,
        model: ModelWandbWrapper,
        framework_model: ModelWandbWrapper,
        embedding_model: EmbeddingModel,
        base_path: str,
        memory_cls: type[AssociativeMemory] = AssociativeMemory,
        perceive_cls: type[PerceiveComponent] = PerceiveComponent,
        retrieve_cls: type[RetrieveComponent] = RetrieveComponent,
        store_cls: type[FishingStoreComponent] = FishingStoreComponent,
        reflect_cls: type[FishingReflectComponent] = FishingReflectComponent,
        plan_cls: type[FishingPlanComponent] = FishingPlanComponent,
        act_cls: type[FishingActComponent] = FishingActComponent,
        converse_cls: type[FishingConverseComponent] = FishingConverseComponent,
    ) -> None:
        super().__init__(
            cfg,
            model,
            framework_model,
            embedding_model,
            base_path,
            memory_cls,
            perceive_cls,
            retrieve_cls,
            store_cls,
            reflect_cls,
            plan_cls,
            act_cls,
            converse_cls,
        )
        self.private_conversations = {}

    def set_other_personas(self, other_personas: dict[str, "PersonaAgent"]):
        """This is an existing method in the base PersonaAgent, we'll assume it's called during setup."""
        super().set_other_personas(other_personas)
        # NEW: Populate the keys for the private conversation history
        for name in self.other_personas:
            if name != self.identity.name:
                self.private_conversations[name] = []

    def loop(self, obs: HarvestingObs) -> PersonaAction:
        res = []
        self.current_time = obs.current_time  # update current time

        self.perceive.perceive(obs)
        # phase based game

        if obs.current_location == "lake" and obs.phase == "lake":
            # Stage 1. Pond situation / Stage 2. Fishermen’s decisions
            retireved_memory = self.retrieve.retrieve([obs.current_location], 10)
            if obs.current_resource_num > 0:
                num_resource, html_interactions = self.act.choose_how_many_fish_to_chat(
                    retireved_memory,
                    obs.current_location,
                    obs.current_time,
                    obs.context,
                    range(0, obs.current_resource_num + 1),
                    obs.before_harvesting_sustainability_threshold,
                )
                action = PersonaActionHarvesting(
                    self.agent_id,
                    "lake",
                    num_resource,
                    stats={f"{self.agent_id}_collected_resource": num_resource},
                    html_interactions=html_interactions,
                )
            else:
                num_resource = 0
                action = PersonaActionHarvesting(
                    self.agent_id,
                    "lake",
                    num_resource,
                    stats={},
                    html_interactions="<strong>Framework<strong/>: no fish to catch",
                )
        elif obs.current_location == "lake" and obs.phase == "pool_after_harvesting":
            # dummy action to register observation
            action = PersonaAction(self.agent_id, "lake")
        elif obs.current_location == "restaurant":
            # Stage 3. Social Interaction a)
            other_personas_identities = []
            for agent_id, location in obs.current_location_agents.items():
                if location == "restaurant":
                    other_personas_identities.append(
                        self.other_personas_from_id[agent_id].identity
                    )
            
            all_html_interactions = []
            
            # --- NEW: PRIVATE CONVERSATION PHASE ---
            agents_in_restaurant = [self.other_personas[p.name] for p in other_personas_identities]
            agents_who_can_initiate = agents_in_restaurant[:] # Copy the list
            
            for agent in agents_in_restaurant:
                if agent not in agents_who_can_initiate:
                    continue # This agent is already in a private chat

                # Ask agent if they want to chat
                chosen_target_name, h = agent.converse.decide_private_chat(
                    other_personas_identities,
                    obs.current_location,
                    obs.current_time
                )
                all_html_interactions.append(h)

                if chosen_target_name:
                    target_persona = self.other_personas[chosen_target_name]
                    
                    # Ensure target is also available
                    if target_persona in agents_who_can_initiate:
                        # Remove both from the list of available agents
                        agents_who_can_initiate.remove(agent)
                        agents_who_can_initiate.remove(target_persona)
                        
                        # Initiate the private conversation
                        _, private_html = agent.converse.converse_private(
                            target_persona.identity,
                            obs.current_location,
                            obs.current_time
                        )
                        all_html_interactions.extend(private_html)
            
            # --- EXISTING: GROUP CONVERSATION PHASE ---
            # Now, the group conversation proceeds, but agents have new private memories
            (
                conversation,
                _,
                resource_limit,
                html_interactions,
            ) = self.converse.converse_group(
                other_personas_identities,
                obs.current_location,
                obs.current_time,
                obs.context,
                obs.agent_resource_num,
            )
            all_html_interactions.extend(html_interactions)
            action = PersonaActionChat(
                self.agent_id,
                "restaurant",
                conversation,
                conversation_resource_limit=resource_limit,
                stats={"conversation_resource_limit": resource_limit},
                html_interactions=all_html_interactions,
            )
        elif obs.current_location == "home":
            # Stage 3. Social Interaction b)
            # TODO How what should we reflect, what is the initial focal points?
            self.reflect.run(["harvesting"])
            action = PersonaAction(self.agent_id, "home")

        self.memory.save()  # periodically save memory
        return action