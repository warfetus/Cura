// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.11
import UM 1.5 as UM

Item
{
    id: extruderIconItem

    implicitWidth: UM.Theme.getSize("extruder_icon").width
    implicitHeight: UM.Theme.getSize("extruder_icon").height

    property bool checked: true
    property color materialColor
    property alias textColor: extruderNumberText.color
    property bool extruderEnabled: true
    property alias iconSize: mainIcon.sourceSize
    property string iconVariant: "medium"

    Item
    {
        opacity: extruderEnabled ? 1 : UM.Theme.getColor("extruder_disabled").a
        anchors.fill: parent
        layer.enabled: true // Prevent weird opacity effects.

        UM.RecolorImage
        {
            anchors.fill: parent
            sourceSize: mainIcon.sourceSize

            source: UM.Theme.getIcon("ExtruderColor", iconVariant)
            color: materialColor
        }
        UM.RecolorImage
        {
            id: mainIcon
            anchors.fill: parent
            sourceSize: UM.Theme.getSize("extruder_icon")

            source: UM.Theme.getIcon("Extruder", iconVariant)
            color: extruderNumberText.color
        }

        UM.Label
        {
            id: extruderNumberText
            anchors.centerIn: parent
            text: index + 1
            font: UM.Theme.getFont("small_emphasis")
            width: contentWidth
            height: contentHeight
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
