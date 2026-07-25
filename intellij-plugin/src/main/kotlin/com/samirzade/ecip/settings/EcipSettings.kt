package com.samirzade.ecip.settings

import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.util.xmlb.XmlSerializerUtil

@State(
    name = "EcipSettings",
    storages = [Storage("ecip_lite.xml")]
)
class EcipSettings : PersistentStateComponent<EcipSettings> {
    var apiUrl: String = "http://127.0.0.1:8000"

    override fun getState(): EcipSettings {
        return this
    }

    override fun loadState(state: EcipSettings) {
        XmlSerializerUtil.copyBean(state, this)
    }
}
