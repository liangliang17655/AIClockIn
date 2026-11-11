from dataclasses import dataclass


@dataclass
class Outcome:
    state: str
    earned: float | None = None
    balance: float | None = None
    detail: str = ''

    @property
    def ok(self):
        return self.state in ('成功', '已签到', '未签到')
