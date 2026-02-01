from pydantic import BaseModel

# ============ Binding Models ============


class BindingRoleRole(BaseModel):
    serverId: str
    roleId: str
    nickname: str
    level: int
    isDefault: bool
    isBanned: bool
    serverType: str
    serverName: str


class BindingRole(BaseModel):
    uid: str
    isOfficial: bool
    isDefault: bool
    channelMasterId: str
    channelName: str
    nickName: str
    isDelete: bool
    gameName: str
    gameId: int
    roles: list[BindingRoleRole]
    defaultRole: BindingRoleRole | None = None


class GameBinding(BaseModel):
    appCode: str
    appName: str
    bindingList: list[BindingRole]
    defaultUid: str | None = None


class BindingData(BaseModel):
    list: list[GameBinding]
    serverDefaultBinding: dict


# ============ Attendance (Sign-in) Models ============


class AttendanceResource(BaseModel):
    id: str
    type: str
    name: str
    rarity: int


class AttendanceAward(BaseModel):
    resource: AttendanceResource | None
    count: int
    type: str


class AttendanceData(BaseModel):
    """Response data for attendance API."""

    ts: str
    awards: list[AttendanceAward]


# ============ Player Info Models ============


class PlayerAvatar(BaseModel):
    """Player avatar info."""

    type: str
    id: str


class PlayerSecretary(BaseModel):
    """Player secretary (assistant) info."""

    charId: str
    skinId: str


class PlayerAP(BaseModel):
    """Player AP (sanity) info."""

    current: int
    max: int
    lastApAddTime: int
    completeRecoveryTime: int


class PlayerStatus(BaseModel):
    """Player status info."""

    uid: str
    name: str
    level: int
    avatar: PlayerAvatar | None
    registerTs: int
    mainStageProgress: str
    secretary: PlayerSecretary | None = None
    resume: str
    subscriptionEnd: int
    ap: PlayerAP | None
    storeTs: int
    lastOnlineTs: int
    charCnt: int
    furnitureCnt: int
    skinCnt: int


# ============ Character Models ============


class CharacterSkill(BaseModel):
    """Character skill info."""

    id: str
    specializeLevel: int


class CharacterEquip(BaseModel):
    """Character equipment (module) info."""

    id: str
    level: int


class Character(BaseModel):
    """Character (operator) info."""

    charId: str
    skinId: str
    level: int
    evolvePhase: int
    potentialRank: int
    mainSkillLvl: int
    skills: list[CharacterSkill]
    equip: list[CharacterEquip]
    favorPercent: int
    defaultSkillId: str
    gainTime: int
    defaultEquipId: str


class AssistCharacter(BaseModel):
    """Assist (support) character info."""

    charId: str
    skinId: str
    level: int
    evolvePhase: int
    potentialRank: int
    skillId: str
    mainSkillLvl: int
    specializeLevel: int
    equip: CharacterEquip | None


# ============ Building Models ============


class BuildingBubble(BaseModel):
    """Building bubble info."""

    add: int
    ts: int


class BuildingBubbleInfo(BaseModel):
    """Building bubble container."""

    normal: BuildingBubble | None
    assist: BuildingBubble | None


class BuildingChar(BaseModel):
    """Character in building."""

    charId: str
    ap: int
    lastApAddTime: int
    index: int
    bubble: BuildingBubbleInfo | None
    workTime: int


class TiredChar(BaseModel):
    """Tired character info."""

    charId: str
    ap: int
    lastApAddTime: int
    roomSlotId: str
    index: int
    bubble: BuildingBubbleInfo | None
    workTime: int


class PowerRoom(BaseModel):
    """Power room (发电站) info."""

    slotId: str
    level: int
    chars: list[BuildingChar]


class ManufactureRoom(BaseModel):
    """Manufacture room (制造站) info."""

    slotId: str
    level: int
    chars: list[BuildingChar]
    completeWorkTime: int
    lastUpdateTime: int
    formulaId: str
    capacity: int
    weight: int
    complete: int
    remain: int
    speed: float


class TradingStock(BaseModel):
    """Trading stock item."""

    id: str
    count: int
    type: str


class TradingOrder(BaseModel):
    """Trading order."""

    instId: int
    type: str
    delivery: list[TradingStock]
    gain: TradingStock | None
    isViolated: bool


class TradingRoom(BaseModel):
    """Trading room (贸易站) info."""

    slotId: str
    level: int
    chars: list[BuildingChar]
    completeWorkTime: int
    lastUpdateTime: int
    strategy: str
    stock: list[TradingOrder]
    stockLimit: int


class DormitoryRoom(BaseModel):
    """Dormitory (宿舍) info."""

    slotId: str
    level: int
    chars: list[BuildingChar]
    comfort: int


class ClueInfo(BaseModel):
    """Clue (线索) info for meeting room."""

    own: int
    received: int
    dailyReward: bool
    needReceive: int
    board: list[str]
    sharing: bool
    shareCompleteTime: int


class MeetingRoom(BaseModel):
    """Meeting room (会客室) info."""

    slotId: str
    level: int
    chars: list[BuildingChar]
    clue: ClueInfo | None
    lastUpdateTime: int
    completeWorkTime: int


class HireRoom(BaseModel):
    """Hire room (办公室) info."""

    slotId: str
    level: int
    chars: list[BuildingChar]
    state: int
    refreshCount: int
    completeWorkTime: int
    slotState: int


class TrainingRoom(BaseModel):
    """Training room (训练室) info."""

    slotId: str
    level: int
    trainee: BuildingChar | None
    trainer: BuildingChar | None
    remainPoint: int
    speed: float
    lastUpdateTime: int
    remainSecs: int
    slotState: int


class LaborInfo(BaseModel):
    """Labor (无人机) info."""

    maxValue: int
    value: int
    lastUpdateTime: int
    remainSecs: int


class FurnitureInfo(BaseModel):
    """Furniture info."""

    total: int


class ElevatorInfo(BaseModel):
    """Elevator info."""

    slotId: str
    slotState: int
    level: int


class CorridorInfo(BaseModel):
    """Corridor info."""

    slotId: str
    slotState: int
    level: int


class ControlRoom(BaseModel):
    """Control room (控制中枢) info."""

    slotId: str
    slotState: int
    level: int
    chars: list[BuildingChar]


class Building(BaseModel):
    """Building (基建) data."""

    tiredChars: list[TiredChar]
    powers: list[PowerRoom]
    manufactures: list[ManufactureRoom]
    tradings: list[TradingRoom]
    dormitories: list[DormitoryRoom]
    meeting: MeetingRoom | None
    hire: HireRoom | None
    training: TrainingRoom | None
    labor: LaborInfo | None
    furniture: FurnitureInfo | None
    elevators: list[ElevatorInfo]
    corridors: list[CorridorInfo]
    control: ControlRoom | None


# ============ Recruit Models ============


class RecruitSlot(BaseModel):
    """Recruit slot info."""

    startTs: int
    finishTs: int
    state: int


# ============ Campaign Models ============


class CampaignRecord(BaseModel):
    """Campaign (剿灭) record."""

    campaignId: str
    maxKills: int


class CampaignReward(BaseModel):
    """Campaign reward info."""

    current: int
    total: int


class Campaign(BaseModel):
    """Campaign (剿灭) data."""

    records: list[CampaignRecord]
    reward: CampaignReward | None


# ============ Tower Models ============


class TowerRewardItem(BaseModel):
    """Tower reward item info."""

    current: int
    total: int


class TowerReward(BaseModel):
    """Tower (保全派驻) reward info."""

    higherItem: TowerRewardItem | None
    lowerItem: TowerRewardItem | None
    termTs: int


class Tower(BaseModel):
    """Tower (保全派驻) data."""

    records: list
    reward: TowerReward | None


# ============ Rogue Models ============


class RogueBank(BaseModel):
    """Rogue (肉鸽) bank info."""

    current: int
    record: int


class RogueRecord(BaseModel):
    """Rogue (肉鸽) record."""

    rogueId: str
    relicCnt: int
    bank: RogueBank | None


class Rogue(BaseModel):
    """Rogue (肉鸽) data."""

    records: list[RogueRecord]


# ============ Routine Models ============


class RoutineTask(BaseModel):
    """Routine task progress."""

    current: int
    total: int


class Routine(BaseModel):
    """Routine (日常/周常) data."""

    daily: RoutineTask | None
    weekly: RoutineTask | None


# ============ Activity Models ============


class ActivityZone(BaseModel):
    """Activity zone info."""

    zoneId: str
    zoneReplicaId: str
    clearedStage: int
    totalStage: int


class Activity(BaseModel):
    """Activity (别传/活动) data."""

    actId: str
    actReplicaId: str
    zones: list[ActivityZone]


# ============ Info Map Models ============


class CharInfo(BaseModel):
    """Character info from info map."""

    id: str
    name: str
    nationId: str
    groupId: str
    displayNumber: str
    rarity: int
    profession: str
    subProfessionId: str


class SkinInfo(BaseModel):
    """Skin info from info map."""

    id: str
    brandId: str
    sortId: int
    displayTagId: str


class EquipmentInfo(BaseModel):
    """Equipment info from info map."""

    id: str
    name: str
    typeIcon: str
    typeName2: str
    shiningColor: str


# ============ Show Config ============


class ShowConfig(BaseModel):
    """Show config for player profile."""

    charSwitch: bool
    skinSwitch: bool
    standingsSwitch: bool


# ============ Skin Data ============


class SkinData(BaseModel):
    """Skin data with acquisition time."""

    id: str
    ts: int


# ============ Main Player Data Model ============


class PlayerData(BaseModel):
    """Complete player data from player info API."""

    currentTs: int
    showConfig: ShowConfig | None
    status: PlayerStatus | None
    assistChars: list[AssistCharacter]
    chars: list[Character]
    skins: list[SkinData]
    building: Building | None
    recruit: list[RecruitSlot]
    campaign: Campaign | None
    tower: Tower | None
    rogue: Rogue | None
    routine: Routine | None
    activity: list[Activity]
    charInfoMap: dict[str, CharInfo]
    skinInfoMap: dict[str, SkinInfo]
    equipmentInfoMap: dict[str, EquipmentInfo]
